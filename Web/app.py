import os
import subprocess
import time

import docker
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)


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


@app.route("/api/containers", methods=["GET"])
def get_containers():
    if client is None:
        return jsonify({"error": "OrbStack 客户端未初始化"}), 500

    try:
        containers = client.containers.list(all=True)
        container_list = []
        for container in containers:
            container_list.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0]
                    if container.image.tags
                    else container.image.id,
                }
            )
        return jsonify({"status": "success", "containers": container_list})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


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
                "attacker",
            ],
            cwd=machines_dir,
            check=True,
        )
        return jsonify(
            {"status": "success", "message": "Attacker started successfully"}
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
