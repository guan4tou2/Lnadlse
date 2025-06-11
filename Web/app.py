import os
import re
import subprocess
import sys
import time

import docker
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from requests.exceptions import RequestException

# 加载环境变量
load_dotenv()

app = Flask(__name__)

# 获取 Elasticsearch 密码
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
app.config["TEMPLATES_AUTO_RELOAD"] = True


def get_docker_socket_path():
    """获取 Docker socket 路径"""
    # 检查不同的平台和工具
    socket_paths = {
        "darwin": [
            "/Users/guantou/.orbstack/run/docker.sock",  # OrbStack
            "/var/run/docker.sock",  # Docker Desktop
            "/Users/guantou/.docker/run/docker.sock",  # Colima
        ],
        "linux": [
            "/var/run/docker.sock",  # 标准 Linux
            "/run/user/1000/docker.sock",  # 用户级 Docker
        ],
        "win32": [
            "//./pipe/docker_engine",  # Windows Docker Desktop
        ],
    }

    # 获取当前平台
    platform = sys.platform
    if platform not in socket_paths:
        platform = "linux"  # 默认使用 Linux 路径

    # 检查所有可能的路径
    for path in socket_paths[platform]:
        if os.path.exists(path):
            return path

    # 如果没有找到任何可用的 socket，返回默认路径
    return socket_paths[platform][0]


def init_docker_client():
    """初始化 Docker 客户端"""
    try:
        socket_path = get_docker_socket_path()
        client = docker.DockerClient(base_url=f"unix://{socket_path}")
        # 测试连接
        client.ping()
        return client
    except Exception as e:
        print(f"Docker client initialization failed: {str(e)}")
        return None


# 初始化 Docker 客户端
try:
    client = init_docker_client()
except Exception as e:
    print(f"Docker client initialization failed: {str(e)}")
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
            "target": {  # 匹配 target-nginx
                "type": "Web",
                "url_template": "http://{ip}:80",
                "credentials": None,
            },
            "elk-es": {  # 匹配 elk-es01-1
                "type": "Web",
                "url_template": "https://{ip}:9200",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
            "elk-kibana": {  # 匹配 elk-kibana-1
                "type": "Web",
                "url_template": "http://{ip}:5601",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
            "attacker": {  # 匹配 attacker-kali-novnc
                "type": "Web VNC",
                "url_template": "http://{ip}:8080/vnc.html",
                "credentials": {"username": "kali", "password": "kalilinux"},
            },
        }

        for container in containers:
            container_name = container.name.lower()
            is_elk = any(prefix in container_name for prefix in elk_prefixes)
            is_simulation = any(
                prefix in container_name for prefix in simulation_prefixes
            )

            if not (is_elk or is_simulation):
                continue

            # 获取容器的 IP 地址
            ip_addresses = {}
            try:
                container_info = container.attrs
                networks = container_info.get("NetworkSettings", {}).get("Networks", {})
                for network_name, network_info in networks.items():
                    ip_addresses[network_name] = network_info.get("IPAddress", "N/A")
            except Exception as e:
                print(f"Error getting container IP: {e}")

            # 确定容器所属的集群
            cluster = "elk" if is_elk else "simulation"

            # 获取连接信息
            connection = None
            for template_name, template in connection_templates.items():
                # 检查容器名称是否匹配模板名称（忽略数字后缀）
                base_name = "".join(
                    c for c in container_name if not c.isdigit()
                ).rstrip("-")
                if template_name in base_name:
                    print(
                        f"Found matching template for {container_name}: {template_name}"
                    )
                    # 使用 elk_net 网络的 IP 地址（如果存在）
                    ip = ip_addresses.get(
                        "elk_net", next(iter(ip_addresses.values()), "N/A")
                    )
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
        # 检查 ELK 环境是否已经在运行
        client = docker.from_env()
        elk_containers = [
            container
            for container in client.containers.list(all=True)
            if any(
                prefix in container.name.lower()
                for prefix in ["elk", "elasticsearch", "logstash", "kibana"]
            )
        ]

        if elk_containers:
            running_containers = [
                container
                for container in elk_containers
                if container.status == "running"
            ]
            if running_containers:
                return jsonify(
                    {
                        "status": "warning",
                        "message": "ELK Stack is already running",
                    }
                )

        # 启动 ELK 环境
        elk_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ELK")
        compose_cmd = get_docker_compose_command()
        subprocess.run(compose_cmd + ["up", "-d"], cwd=elk_dir, check=True)

        return jsonify(
            {
                "status": "success",
                "message": "ELK Stack started successfully",
            }
        )
    except Exception as e:
        print(f"Error starting ELK Stack: {str(e)}")
        return jsonify(
            {"status": "error", "message": f"Error starting ELK Stack: {str(e)}"}
        ), 500


def get_docker_compose_command():
    """获取 docker-compose 命令"""
    # 检查是否安装了 docker compose 插件
    try:
        subprocess.run(
            ["docker", "compose", "version"], capture_output=True, check=True
        )
        return ["docker", "compose"]
    except:
        # 如果没有插件，尝试使用独立的 docker-compose
        try:
            subprocess.run(
                ["docker-compose", "version"], capture_output=True, check=True
            )
            return ["docker-compose"]
        except:
            raise Exception(
                "Neither 'docker compose' plugin nor 'docker-compose' command found"
            )


def get_elasticsearch_ip():
    """获取 Elasticsearch 容器的 IP 地址"""
    try:
        client = docker.from_env()
        container = client.containers.get("elk-es01-1")
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        for network_name, network_info in networks.items():
            if network_name == "elk_net":
                return network_info.get("IPAddress")
        return None
    except Exception as e:
        print(f"获取 Elasticsearch IP 失败: {str(e)}")
        return None


def update_packetbeat_config(es_ip):
    """更新 packetbeat 配置文件"""
    try:
        # 获取 packetbeat.yml 文件路径
        beat_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines", "Beat"
        )
        packetbeat_path = os.path.join(beat_dir, "packetbeat.yml")

        # 读取配置文件
        with open(packetbeat_path, "r") as f:
            content = f.read()

        # 更新 Elasticsearch 主机地址
        content = re.sub(
            r'hosts: \[".*?"\]', f'hosts: ["https://{es_ip}:9200"]', content
        )

        # 更新用户名
        content = re.sub(r'#username: "elastic"', 'username: "elastic"', content)

        # 写入更新后的配置
        with open(packetbeat_path, "w") as f:
            f.write(content)

        return True, "packetbeat 配置更新成功"
    except Exception as e:
        return False, f"更新 packetbeat 配置失败: {str(e)}"


def check_elk_status(max_retries=5, retry_delay=10):
    """检查 ELK 环境是否正常运行，包含重试机制"""
    for attempt in range(max_retries):
        try:
            print(f"尝试检查 ELK 环境 (第 {attempt + 1} 次)")

            # 获取 Elasticsearch IP
            es_ip = get_elasticsearch_ip()
            if not es_ip:
                print("无法获取 Elasticsearch IP")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, "无法获取 Elasticsearch IP"

            # 检查 Elasticsearch 是否运行
            es_url = f"https://{es_ip}:9200"
            print(f"检查 Elasticsearch: {es_url}")
            es_response = requests.get(
                es_url, auth=("elastic", ELASTIC_PASSWORD), verify=False, timeout=10
            )
            if es_response.status_code != 200:
                print(f"Elasticsearch 未就绪，状态码: {es_response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, "Elasticsearch 未正常运行"

            # 获取 Kibana IP
            try:
                kibana_container = client.containers.get("elk-kibana-1")
                kibana_networks = kibana_container.attrs.get("NetworkSettings", {}).get(
                    "Networks", {}
                )
                kibana_ip = next(
                    (
                        info.get("IPAddress")
                        for name, info in kibana_networks.items()
                        if name == "elk_net"
                    ),
                    None,
                )
            except Exception as e:
                print(f"获取 Kibana IP 失败: {str(e)}")
                kibana_ip = None

            if not kibana_ip:
                print("无法获取 Kibana IP")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, "无法获取 Kibana IP"

            # 检查 Kibana 是否运行
            kibana_url = f"http://{kibana_ip}:5601"
            print(f"检查 Kibana: {kibana_url}")
            kibana_response = requests.get(kibana_url, timeout=10)
            if kibana_response.status_code != 200:
                print(f"Kibana 未就绪，状态码: {kibana_response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, "Kibana 未正常运行"

            # 更新 packetbeat 配置
            update_success, update_message = update_packetbeat_config(es_ip)
            if not update_success:
                print(f"警告: {update_message}")

            return True, "ELK 环境正常运行"
        except RequestException as e:
            print(f"检查失败 (第 {attempt + 1} 次): {str(e)}")
            if attempt < max_retries - 1:
                print(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                return False, f"ELK 环境检查失败: {str(e)}"
    return False, "ELK 环境检查超时"


@app.route("/api/start_target", methods=["POST"])
def start_target():
    try:
        # 首先检查 ELK 环境状态
        elk_ok, elk_message = check_elk_status()
        if not elk_ok:
            return jsonify(
                {"status": "error", "message": f"无法启动目标机器: {elk_message}"}
            ), 400

        target_type = request.json.get("type")
        if target_type not in ["nginx", "httpd"]:
            return jsonify({"error": "Invalid target type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        compose_cmd = get_docker_compose_command()
        subprocess.run(
            compose_cmd
            + [
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                "--build",
                f"target-{target_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {
                "status": "success",
                "message": f"{target_type} 目标机器启动成功",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_attacker", methods=["POST"])
def start_attacker():
    try:
        # 首先检查 ELK 环境状态
        elk_ok, elk_message = check_elk_status()
        if not elk_ok:
            return jsonify(
                {"status": "error", "message": f"无法启动攻击机器: {elk_message}"}
            ), 400

        attacker_type = request.json.get("type")
        if attacker_type not in ["kali-novnc", "kali-xrdp", "kali-x11"]:
            return jsonify({"error": "Invalid attacker type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        compose_cmd = get_docker_compose_command()
        subprocess.run(
            compose_cmd
            + [
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                "--build",
                f"attacker-{attacker_type}",
            ],
            cwd=machines_dir,
            check=True,
        )
        return jsonify(
            {
                "status": "success",
                "message": f"{attacker_type} 攻击机器启动成功",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop_all", methods=["POST"])
def stop_all():
    try:
        compose_cmd = get_docker_compose_command()

        # Stop ELK
        elk_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ELK")
        subprocess.run(compose_cmd + ["down", "-v"], cwd=elk_dir, check=True)

        # Stop simulation environment
        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        subprocess.run(
            compose_cmd + ["-f", "docker-compose-simulation.yml", "down", "-v"],
            cwd=machines_dir,
            check=True,
        )

        # Force stop any remaining containers
        client = docker.from_env()
        containers = client.containers.list(all=True)
        for container in containers:
            try:
                container.stop()
                container.remove()
            except Exception as e:
                print(f"Error stopping container {container.name}: {e}")

        return jsonify(
            {"status": "success", "message": "All services stopped successfully"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_simulation", methods=["POST"])
def start_simulation():
    try:
        # 暂时跳过 ELK 环境检查
        # elk_ok, elk_message = check_elk_status()
        # if not elk_ok:
        #     return jsonify(
        #         {"status": "error", "message": f"Cannot start simulation: {elk_message}"}
        #     ), 400

        target_type = request.json.get("target_type")
        attacker_type = request.json.get("attacker_type")

        if not target_type or not attacker_type:
            return jsonify(
                {
                    "status": "error",
                    "message": "Target type and attacker type are required",
                }
            ), 400

        if target_type not in ["nginx", "httpd"]:
            return jsonify({"status": "error", "message": "Invalid target type"}), 400

        if attacker_type not in ["kali-novnc", "kali-xrdp", "kali-x11"]:
            return jsonify({"status": "error", "message": "Invalid attacker type"}), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        compose_cmd = get_docker_compose_command()

        # 同时启动目标和攻击机器
        subprocess.run(
            compose_cmd
            + [
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                "--build",
                f"target-{target_type}",
                f"attacker-{attacker_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {
                "status": "success",
                "message": f"Simulation environment started with target: {target_type}, attacker: {attacker_type}",
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
