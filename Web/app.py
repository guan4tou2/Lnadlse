import os
import subprocess
import time

import docker
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 尝试从环境变量获取 Elasticsearch 密码
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")  # 默认密码为 changeme
app.config["TEMPLATES_AUTO_RELOAD"] = True


def init_docker_client():
    """初始化 Docker 客户端，包含重试逻辑"""
    max_retries = 3
    retry_delay = 2  # 秒

    # 设置 Docker 环境变量
    socket_path = "/Users/guantou/.orbstack/run/docker.sock"
    if not os.path.exists(socket_path):
        raise Exception(f"OrbStack socket 文件不存在: {socket_path}")

    os.environ["DOCKER_HOST"] = f"unix://{socket_path}"

    for attempt in range(max_retries):
        try:
            # 使用环境变量配置
            client = docker.from_env()
            # 测试连接
            client.ping()
            print("成功连接到 OrbStack")
            return client
        except docker.errors.DockerException as e:
            if attempt < max_retries - 1:
                print(
                    f"OrbStack 连接尝试 {attempt + 1} 失败，等待 {retry_delay} 秒后重试..."
                )
                print(f"错误信息: {str(e)}")
                time.sleep(retry_delay)
            else:
                print("无法连接到 OrbStack，请确保 OrbStack 正在运行")
                raise


# 初始化 Docker 客户端
try:
    client = init_docker_client()
except Exception as e:
    print(f"OrbStack 客户端初始化失败: {str(e)}")
    client = None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/networks", methods=["GET"])
def get_networks():
    try:
        client = docker.from_env()
        networks = client.networks.list()
        network_list = []

        # 定义相关容器名称前缀
        elk_prefixes = ["elk", "elasticsearch", "logstash", "kibana"]
        simulation_prefixes = ["target", "attacker"]

        # 获取所有相关容器
        containers = client.containers.list(all=True)
        relevant_containers = []
        for container in containers:
            container_name = container.name.lower()
            is_elk = any(prefix in container_name for prefix in elk_prefixes)
            is_simulation = any(
                prefix in container_name for prefix in simulation_prefixes
            )
            if is_elk or is_simulation:
                relevant_containers.append(container)

        # 获取相关容器所在的网络
        for network in networks:
            network_containers = []
            for container in relevant_containers:
                try:
                    # 检查容器是否在这个网络中
                    container_info = container.attrs
                    container_networks = container_info.get("NetworkSettings", {}).get(
                        "Networks", {}
                    )
                    if network.name in container_networks:
                        network_containers.append(
                            {
                                "id": container.id[:12],
                                "name": container.name,
                                "status": container.status,
                            }
                        )
                except Exception as e:
                    print(f"Error getting container info: {e}")
                    continue

            # 只添加包含相关容器的网络
            if network_containers:
                network_list.append(
                    {
                        "id": network.id[:12],
                        "name": network.name,
                        "driver": network.attrs["Driver"],
                        "containers": network_containers,
                    }
                )

        return jsonify(network_list)
    except Exception as e:
        print(f"Error in get_networks: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/containers", methods=["GET"])
def get_containers():
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        container_list = []

        # 定义相关容器名称前缀
        elk_prefixes = ["elk", "elasticsearch", "logstash", "kibana"]
        simulation_prefixes = ["target", "attacker"]

        # 定义容器的连接信息模板
        connection_templates = {
            "target-nginx": {  # 修改为匹配 target-nginx
                "type": "Web",
                "url_template": "http://{ip}",
                "credentials": None,
            },
            "attacker": {  # 修改为匹配 attacker-1
                "type": "Web VNC",
                "url_template": "http://{ip}:8080/vnc.html",
                "credentials": {"username": "kali", "password": "kali"},
            },
            "elk-es01": {  # 修改为匹配 elk-es01-1
                "type": "Web",
                "url_template": "https://{ip}:9200",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
            "elk-kibana": {  # 保持匹配 elk-kibana-1
                "type": "Web",
                "url_template": "http://{ip}:5601",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
        }

        for container in containers:
            # 检查容器是否属于我们的环境
            container_name = container.name.lower()
            print(f"Processing container: {container_name}")

            is_elk = any(prefix in container_name for prefix in elk_prefixes)
            is_simulation = any(
                prefix in container_name for prefix in simulation_prefixes
            )

            if not (is_elk or is_simulation):
                continue

            # 获取容器的网络设置
            container_info = container.attrs
            networks = container_info.get("NetworkSettings", {}).get("Networks", {})
            ip_addresses = {}

            # 获取每个网络的 IP 地址
            for network_name, network_info in networks.items():
                ip = network_info.get("IPAddress", "N/A")
                ip_addresses[network_name] = ip
                print(f"Network {network_name} IP: {ip}")

            # 确定容器所属集群
            cluster = "elk" if is_elk else "simulation"

            # 获取容器的连接信息
            connection = None
            for key, template in connection_templates.items():
                if key in container_name:
                    print(f"Found matching template for {container_name}: {key}")
                    # 使用第一个可用的 IP 地址
                    ip = next(iter(ip_addresses.values()), "N/A")
                    if ip != "N/A":
                        connection = {
                            "type": template["type"],
                            "url": template["url_template"].format(ip=ip),
                            "credentials": template["credentials"],
                        }
                        print(f"Generated connection info: {connection}")
                    else:
                        print(f"No IP address found for {container_name}")
                    break

            container_data = {
                "id": container.id[:12],
                "name": container.name,
                "status": container.status,
                "image": container.image.tags[0]
                if container.image.tags
                else container.image.id[:12],
                "ip_addresses": ip_addresses,
                "cluster": cluster,
                "connection": connection,
            }
            print(f"Container data: {container_data}")
            container_list.append(container_data)

        return jsonify(container_list)
    except Exception as e:
        print(f"Error in get_containers: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/start_elk", methods=["POST"])
def start_elk():
    try:
        elk_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ELK")
        subprocess.run(["docker-compose", "up", "-d"], cwd=elk_dir, check=True)
        return jsonify(
            {"status": "success", "message": "ELK Stack started successfully"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_target", methods=["POST"])
def start_target():
    try:
        target_type = request.json.get("type")
        if target_type not in ["nginx", "httpd"]:
            return jsonify({"error": "Invalid target type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                f"target-{target_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {
                "status": "success",
                "message": f"{target_type} target started successfully",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_attacker", methods=["POST"])
def start_attacker():
    try:
        attacker_type = request.json.get("type")
        if attacker_type not in ["kali-novnc", "kali-xrdp", "kali-x11"]:
            return jsonify({"error": "Invalid attacker type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                f"attacker-{attacker_type}",
            ],
            cwd=machines_dir,
            check=True,
        )
        return jsonify(
            {
                "status": "success",
                "message": f"{attacker_type} attacker started successfully",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop_all", methods=["POST"])
def stop_all():
    try:
        # Stop ELK
        elk_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ELK")
        subprocess.run(["docker-compose", "down"], cwd=elk_dir, check=True)

        # Stop simulation environment
        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        subprocess.run(
            ["docker-compose", "-f", "docker-compose-simulation.yml", "down"],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {"status": "success", "message": "All services stopped successfully"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_simulation", methods=["POST"])
def start_simulation():
    try:
        target_type = request.json.get("target_type")
        attacker_type = request.json.get("attacker_type")

        if not target_type or not attacker_type:
            return jsonify({"error": "Target type and attacker type are required"}), 400

        if target_type not in ["nginx", "httpd"]:
            return jsonify({"error": "Invalid target type"}), 400

        if attacker_type not in ["kali-novnc", "kali-xrdp", "kali-x11"]:
            return jsonify({"error": "Invalid attacker type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )

        # 启动目标机器
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                f"target-{target_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        # 启动攻击机器
        subprocess.run(
            [
                "docker-compose",
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                f"attacker-{attacker_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {
                "status": "success",
                "message": f"Simulation environment started with {target_type} target and {attacker_type} attacker",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/containers/<container_id>/stop", methods=["POST"])
def stop_container(container_id):
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
