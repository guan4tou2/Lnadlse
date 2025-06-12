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

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Get Elasticsearch password
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "changeme")
app.config["TEMPLATES_AUTO_RELOAD"] = True


def get_docker_socket_path():
    """Get Docker socket path"""
    # Check different platforms and tools
    socket_paths = {
        "darwin": [
            "~/.orbstack/run/docker.sock",  # OrbStack
            "/var/run/docker.sock",  # Docker Desktop
            "~/.docker/run/docker.sock",  # Colima
        ],
        "linux": [
            "/var/run/docker.sock",  # Standard Linux
            "/run/user/1000/docker.sock",  # User-level Docker
        ],
        "win32": [
            "//./pipe/docker_engine",  # Windows Docker Desktop
        ],
    }

    # Get current platform
    platform = sys.platform
    if platform not in socket_paths:
        platform = "linux"  # Default to Linux path

    # Check all possible paths
    for path in socket_paths[platform]:
        if os.path.exists(path):
            return path

    # If no socket found, return default path
    return socket_paths[platform][0]


def init_docker_client():
    """Initialize Docker client"""
    try:
        socket_path = get_docker_socket_path()
        client = docker.DockerClient(base_url=f"unix://{socket_path}")
        # Test connection
        client.ping()
        return client
    except Exception as e:
        print(f"Docker client initialization failed: {str(e)}")
        return None


# Initialize Docker client
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

        # Define related container name prefixes
        elk_prefixes = ["elk", "elasticsearch", "logstash", "kibana"]
        simulation_prefixes = ["target", "attacker"]

        # Get all related containers
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

        # Get networks related to containers
        for network in networks:
            network_containers = []
            for container in relevant_containers:
                try:
                    # Check if container is in this network
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

            # Only add networks containing relevant containers
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

        # Define related container name prefixes
        elk_prefixes = ["elk", "elasticsearch", "logstash", "kibana"]
        simulation_prefixes = ["target", "attacker"]

        # Define container connection information template
        connection_templates = {
            "target": {  # Match target-nginx
                "type": "Web",
                "url_template": "http://{ip}:80",
                "credentials": None,
            },
            "elk-es": {  # Match elk-es01-1
                "type": "Web",
                "url_template": "https://{ip}:9200",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
            "elk-kibana": {  # Match elk-kibana-1
                "type": "Web",
                "url_template": "http://{ip}:5601",
                "credentials": {"username": "elastic", "password": ELASTIC_PASSWORD},
            },
            "attacker": {  # Match attacker-kali-novnc
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

            # Get container IP addresses
            ip_addresses = {}
            try:
                container_info = container.attrs
                networks = container_info.get("NetworkSettings", {}).get("Networks", {})
                for network_name, network_info in networks.items():
                    ip_addresses[network_name] = network_info.get("IPAddress", "N/A")
            except Exception as e:
                print(f"Error getting container IP: {e}")

            # Determine container cluster
            cluster = "elk" if is_elk else "simulation"

            # Get connection information
            connection = None
            for template_name, template in connection_templates.items():
                # Check if container name matches template name (ignoring digit suffix)
                base_name = "".join(
                    c for c in container_name if not c.isdigit()
                ).rstrip("-")
                if template_name in base_name:
                    print(
                        f"Found matching template for {container_name}: {template_name}"
                    )
                    # Use IP address from elk_net network (if exists)
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
        # Check if ELK environment is already running
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

        # Start ELK environment
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
    """Get docker-compose command"""
    # Check if docker compose plugin is installed
    try:
        subprocess.run(
            ["docker", "compose", "version"], capture_output=True, check=True
        )
        return ["docker", "compose"]
    except:
        # If no plugin, try using standalone docker-compose
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
    """Get Elasticsearch container IP address"""
    try:
        client = docker.from_env()
        container = client.containers.get("elk-es01-1")
        networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
        for network_name, network_info in networks.items():
            if network_name == "elk_net":
                return network_info.get("IPAddress")
        return None
    except Exception as e:
        print(f"Failed to get Elasticsearch IP: {str(e)}")
        return None


def update_packetbeat_config(es_ip):
    """Update packetbeat configuration"""
    try:
        # Get packetbeat.yml file path
        beat_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines", "Beat"
        )
        packetbeat_path = os.path.join(beat_dir, "packetbeat.yml")

        # Read configuration file
        with open(packetbeat_path, "r") as f:
            content = f.read()

        # Update Elasticsearch host address
        content = re.sub(
            r'hosts: \[".*?"\]', f'hosts: ["https://{es_ip}:9200"]', content
        )

        # Update username
        content = re.sub(r'#username: "elastic"', 'username: "elastic"', content)

        # Write updated configuration
        with open(packetbeat_path, "w") as f:
            f.write(content)

        return True, "Packetbeat configuration updated successfully"
    except Exception as e:
        return False, f"Failed to update packetbeat configuration: {str(e)}"


def check_elk_status(max_retries=5, retry_delay=10):
    """Check if ELK environment is running properly, with retry mechanism"""
    for attempt in range(max_retries):
        try:
            print(f"Checking ELK environment (Attempt {attempt + 1})")

            # Get Elasticsearch IP
            es_ip = get_elasticsearch_ip()
            if not es_ip:
                print("Unable to get Elasticsearch IP")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, {
                    "code": "ES_IP_NOT_FOUND",
                    "message": "Unable to get Elasticsearch IP",
                    "details": "Elasticsearch container might not be running or network configuration is incorrect",
                }

            # Check if Elasticsearch is running
            es_url = f"https://{es_ip}:9200"
            print(f"Checking Elasticsearch: {es_url}")
            es_response = requests.get(
                es_url, auth=("elastic", ELASTIC_PASSWORD), verify=False, timeout=10
            )
            if es_response.status_code != 200:
                print(
                    f"Elasticsearch not ready, status code: {es_response.status_code}"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, {
                    "code": "ES_NOT_READY",
                    "message": "Elasticsearch not running properly",
                    "details": f"Status code: {es_response.status_code}, Response: {es_response.text}",
                }

            # Get Kibana IP
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
                print(f"Failed to get Kibana IP: {str(e)}")
                kibana_ip = None

            if not kibana_ip:
                print("Unable to get Kibana IP")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, {
                    "code": "KIBANA_IP_NOT_FOUND",
                    "message": "Unable to get Kibana IP",
                    "details": "Kibana container might not be running or network configuration is incorrect",
                }

            # Check if Kibana is running
            kibana_url = f"http://{kibana_ip}:5601"
            print(f"Checking Kibana: {kibana_url}")
            kibana_response = requests.get(kibana_url, timeout=10)
            if kibana_response.status_code != 200:
                print(f"Kibana not ready, status code: {kibana_response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                return False, {
                    "code": "KIBANA_NOT_READY",
                    "message": "Kibana not running properly",
                    "details": f"Status code: {kibana_response.status_code}, Response: {kibana_response.text}",
                }

            # Update packetbeat configuration
            update_success, update_message = update_packetbeat_config(es_ip)
            if not update_success:
                print(f"Warning: {update_message}")
                return False, {
                    "code": "PACKETBEAT_CONFIG_FAILED",
                    "message": "Failed to update packetbeat configuration",
                    "details": update_message,
                }

            return True, {
                "code": "SUCCESS",
                "message": "ELK environment running properly",
                "details": "All components are running and properly configured",
            }
        except RequestException as e:
            print(f"Check failed (Attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                print(f"Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
            else:
                return False, {
                    "code": "REQUEST_FAILED",
                    "message": "ELK environment check failed",
                    "details": str(e),
                }
    return False, {
        "code": "CHECK_TIMEOUT",
        "message": "ELK environment check timeout",
        "details": f"Failed after {max_retries} attempts with {retry_delay}s delay between attempts",
    }


@app.route("/api/start_target", methods=["POST"])
def start_target():
    try:
        # First check ELK environment status
        elk_ok, elk_message = check_elk_status()
        if not elk_ok:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Cannot start target machine: {elk_message}",
                }
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
                # "--build",
                f"target-{target_type}",
            ],
            cwd=machines_dir,
            check=True,
        )

        return jsonify(
            {
                "status": "success",
                "message": f"{target_type} target machine started successfully",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_attacker", methods=["POST"])
def start_attacker():
    try:
        # First check ELK environment status
        elk_ok, elk_message = check_elk_status()
        if not elk_ok:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Cannot start attacker machine: {elk_message}",
                }
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
                # "--build",
                f"attacker-{attacker_type}",
            ],
            cwd=machines_dir,
            check=True,
        )
        return jsonify(
            {
                "status": "success",
                "message": f"{attacker_type} attacker machine started successfully",
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


@app.route("/api/stop_simulation", methods=["POST"])
def stop_simulation():
    try:
        compose_cmd = get_docker_compose_command()

        # Stop simulation environment
        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        subprocess.run(
            compose_cmd + ["-f", "docker-compose-simulation.yml", "down", "-v"],
            cwd=machines_dir,
            check=True,
        )

        # Force stop any remaining simulation containers
        client = docker.from_env()
        containers = client.containers.list(all=True)
        simulation_prefixes = ["target", "attacker"]
        for container in containers:
            container_name = container.name.lower()
            if any(prefix in container_name for prefix in simulation_prefixes):
                try:
                    container.stop()
                    container.remove()
                except Exception as e:
                    print(f"Error stopping container {container.name}: {e}")

        return jsonify(
            {
                "status": "success",
                "message": "Simulation environment stopped successfully",
            }
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop_elk", methods=["POST"])
def stop_elk():
    try:
        compose_cmd = get_docker_compose_command()

        # Stop ELK
        elk_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ELK")
        subprocess.run(compose_cmd + ["down", "-v"], cwd=elk_dir, check=True)

        # Force stop any remaining ELK containers
        client = docker.from_env()
        containers = client.containers.list(all=True)
        elk_prefixes = ["elk", "elasticsearch", "logstash", "kibana"]
        for container in containers:
            container_name = container.name.lower()
            if any(prefix in container_name for prefix in elk_prefixes):
                try:
                    container.stop()
                    container.remove()
                except Exception as e:
                    print(f"Error stopping container {container.name}: {e}")

        return jsonify(
            {"status": "success", "message": "ELK Stack stopped successfully"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/start_simulation", methods=["POST"])
def start_simulation():
    try:
        # Check ELK environment status
        elk_ok, elk_status = check_elk_status()
        if not elk_ok:
            return jsonify({"status": "error", "error": elk_status}), 400

        target_type = request.json.get("target_type")
        attacker_type = request.json.get("attacker_type")

        if not target_type or not attacker_type:
            return jsonify(
                {
                    "status": "error",
                    "error": {
                        "code": "MISSING_PARAMETERS",
                        "message": "Required parameters missing",
                        "details": "Both target_type and attacker_type are required",
                    },
                }
            ), 400

        if target_type not in ["nginx", "httpd"]:
            return jsonify(
                {
                    "status": "error",
                    "error": {
                        "code": "INVALID_TARGET_TYPE",
                        "message": "Invalid target type",
                        "details": f"Target type must be one of: nginx, httpd. Got: {target_type}",
                    },
                }
            ), 400

        if attacker_type not in ["kali-novnc", "kali-xrdp", "kali-x11"]:
            return jsonify(
                {
                    "status": "error",
                    "error": {
                        "code": "INVALID_ATTACKER_TYPE",
                        "message": "Invalid attacker type",
                        "details": f"Attacker type must be one of: kali-novnc, kali-xrdp, kali-x11. Got: {attacker_type}",
                    },
                }
            ), 400

        machines_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "Machines"
        )
        compose_cmd = get_docker_compose_command()

        # Start both target and attacker machines simultaneously
        subprocess.run(
            compose_cmd
            + [
                "-f",
                "docker-compose-simulation.yml",
                "up",
                "-d",
                # "--build",
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
                "details": {"target_type": target_type, "attacker_type": attacker_type},
            }
        )
    except subprocess.CalledProcessError as e:
        return jsonify(
            {
                "status": "error",
                "error": {
                    "code": "DOCKER_COMPOSE_FAILED",
                    "message": "Failed to start simulation environment",
                    "details": f"Docker Compose command failed: {str(e)}",
                },
            }
        ), 500
    except Exception as e:
        return jsonify(
            {
                "status": "error",
                "error": {
                    "code": "UNKNOWN_ERROR",
                    "message": "An unexpected error occurred",
                    "details": str(e),
                },
            }
        ), 500


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
