#!/usr/bin/env python3
import subprocess
import time
import re
from pathlib import Path

ENV_PATH = Path(".env")
DOCKER_NETWORK = "elk_net"
ELASTIC_VERSION = "9.0.0"


def get_docker_ip(container_name):
    try:
        result = subprocess.check_output(
            [
                "docker",
                "inspect",
                "-f",
                "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                container_name,
            ],
            text=True,
        ).strip()
        return result or "Not running"
    except subprocess.CalledProcessError:
        return "Not found"


def get_elastic_password():
    if not ENV_PATH.exists():
        return ""
    with open(ENV_PATH) as f:
        for line in f:
            if line.startswith("ELASTIC_PASSWORD="):
                return line.strip().split("=")[1]
    return ""

def containers_exist():
    """Check if any containers are defined in docker-compose and exist."""
    result = subprocess.run(
        ["docker-compose", "ps", "-a", "-q"], capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def install():
    print("[*] Setting up ELK stack...")

    if not ENV_PATH.exists():
        print("[!] .env file not found")
        return

    content = ENV_PATH.read_text()
    new_content = re.sub(
        r"STACK_VERSION=.*", f"STACK_VERSION={ELASTIC_VERSION}", content
    )
    ENV_PATH.write_text(new_content)

    # Create docker network if not exists
    print("[*] Creating docker network...")
    networks_output = subprocess.check_output(["docker", "network", "ls"], text=True).splitlines()
    network_names = [line.split()[1] for line in networks_output[1:] if len(line.split()) > 1]
    if DOCKER_NETWORK not in network_names:
        print(f"[*] Creating docker network {DOCKER_NETWORK}...")
        subprocess.run(["docker", "network", "create", DOCKER_NETWORK])
        print(f"[*] Docker network {DOCKER_NETWORK} created")
    else:
        print(f"[*] Docker network {DOCKER_NETWORK} already exists")

    print("[*] Setted ELK stack")
    print("[*] Run 'start' to start the stack")

    image_names = [f"docker.elastic.co/elasticsearch/elasticsearch:{ELASTIC_VERSION}", f"docker.elastic.co/kibana/kibana:{ELASTIC_VERSION}"]
    for image_name in image_names:
        if not subprocess.run(["docker", "images", "-q", image_name], capture_output=True, text=True).stdout.strip():
            print(f"[*] Pulling {image_name} image...")
            subprocess.run(["docker", "pull", image_name])
            print(f"[*] {image_name} image pulled")


def show():
    print("Kibana IP:", get_docker_ip("elk-kibana-1"))
    print("Elasticsearch IP:", get_docker_ip("elk-es01-1"))


def start():
    if containers_exist():
        print("[*] Starting existing containers...")
        subprocess.run(["docker-compose", "start"])
    else:
        print("[*] No containers found, running 'docker-compose up -d'...")
        subprocess.run(["docker-compose", "up", "-d"])

    print("[*] Waiting for services to initialize...")
    time.sleep(30)
    show()
    check()


def stop():
    subprocess.run(["docker-compose", "stop"])


def remove():
    subprocess.run(["docker-compose", "down", "-v"])


def check():
    print("[*] Checking Elasticsearch connection...")
    password = get_elastic_password()
    try:
        output = subprocess.check_output(
            ["curl", "-s", "-k", "https://localhost:9200", "-u", f"elastic:{password}"],
            text=True,
        )
        print(output)
    except subprocess.CalledProcessError:
        print("[!] Connection failed")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["install", "start", "stop", "remove", "show", "check"]
    )
    args = parser.parse_args()

    actions = {
        "install": install,
        "start": start,
        "stop": stop,
        "remove": remove,
        "show": show,
        "check": check,
    }
    actions[args.action]()


if __name__ == "__main__":
    main()
