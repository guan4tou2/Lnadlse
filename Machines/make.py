#!/usr/bin/env python3
import subprocess,os
from pathlib import Path

import os
import subprocess

BASE_DIRS = {"Targeted": "./Targeted", "Attacker": "./Attacker"}

DOCKER_NETWORK = "elk_net"


def find_docker_builds(base_dir):
    docker_paths = []
    for root, dirs, files in os.walk(base_dir):
        if "Dockerfile" in files:
            docker_paths.append(root)
    return docker_paths


def select_path(paths):
    print("Select a Docker build directory:")
    for idx, path in enumerate(paths, 1):
        print(f"{idx}. {path.split('/')[-1]}")
    choice = input("Enter number (or Enter to cancel): ").strip()
    if (
        not choice
        or not choice.isdigit()
        or int(choice) < 1
        or int(choice) > len(paths)
    ):
        print("[!] Invalid selection or cancelled.")
        return None
    return paths[int(choice) - 1]


def build_image(path, image_prefix):
    # 將 tag 轉為小寫字母
    tag = f"{image_prefix}_{os.path.basename(path)}".lower()
    dockerfile_path = os.path.join(path, "Dockerfile")
    print(f"[*] Building image: {tag}")
    subprocess.run(
        ["docker", "build", "-t", tag, path, "-f", dockerfile_path], check=True
    )


def ensure_network():
    result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)
    if DOCKER_NETWORK not in result.stdout:
        print(f"[*] Creating network '{DOCKER_NETWORK}'...")
        subprocess.run(["docker", "network", "create", DOCKER_NETWORK], check=True)


def install():
    ensure_network()

    print("Select what to build:")
    print("1. Targeted")
    print("2. Attacker")
    print("3. All")

    choice = input("Enter your choice (1/2/3): ").strip()

    selected_dirs = []
    if choice == "1":
        selected_dirs = [("targeted", BASE_DIRS["Targeted"])]
    elif choice == "2":
        selected_dirs = [("attacker", BASE_DIRS["Attacker"])]
    elif choice == "3":
        selected_dirs = [
            ("targeted", BASE_DIRS["Targeted"]),
            ("attacker", BASE_DIRS["Attacker"]),
        ]
    else:
        print("[!] Invalid choice.")
        return

    for prefix, path in selected_dirs:
        docker_paths = find_docker_builds(path)
        if not docker_paths:
            print(f"[!] No Dockerfiles found in {path}")
            continue
        selected = select_path(docker_paths)
        if selected:
            build_image(selected, prefix)

def create_network():
    print(f"[*] Checking Docker network '{DOCKER_NETWORK}'...")
    result = subprocess.run(["docker", "network", "ls"], capture_output=True, text=True)
    if DOCKER_NETWORK not in result.stdout:
        print(f"[+] Creating Docker network: {DOCKER_NETWORK}")
        subprocess.run(["docker", "network", "create", DOCKER_NETWORK])
    else:
        print("[=] Docker network already exists.")


def start():
    print("[*] Starting containers...")
    subprocess.run(["docker-compose", "start"])


def stop():
    print("[*] Stopping containers...")
    subprocess.run(["docker-compose", "stop"])


def remove():
    print("[*] Removing containers and volumes...")
    subprocess.run(["docker-compose", "down", "-v"])


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["install", "start", "stop", "remove"])
    args = parser.parse_args()

    actions = {"install": install, "start": start, "stop": stop, "remove": remove}

    actions[args.action]()


if __name__ == "__main__":
    main()
