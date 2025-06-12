#!/usr/bin/env python3
import os
import platform
import subprocess

BASE_DIRS = {"Targeted": "./Targeted", "Attacker": "./Attacker"}

DOCKER_NETWORK = "elk_net"

# 默认构建的 Dockerfile 路径
DEFAULT_BUILDS = {"targeted": "./Targeted/nginx", "attacker": "./Attacker/novnc"}


def get_system_architecture():
    """Detect system architecture and return corresponding beat architecture identifier"""
    arch = platform.machine().lower()
    if arch == "x86_64" or arch == "amd64":
        return "x86_64"
    elif arch == "aarch64" or arch == "arm64":
        return "arm64"
    else:
        raise ValueError(f"Unsupported architecture: {arch}")


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
    # Get system architecture
    arch = get_system_architecture()

    # Convert tag to lowercase
    tag = f"{image_prefix}_{os.path.basename(path)}".lower()
    dockerfile_path = os.path.join(path, "Dockerfile")

    # Check if Dockerfile exists
    if not os.path.exists(dockerfile_path):
        print(f"[!] Error: Dockerfile not found: {dockerfile_path}")
        return False

    # Create temporary Dockerfile
    temp_dockerfile = os.path.join(path, "Dockerfile.temp")
    try:
        with open(dockerfile_path, "r") as f:
            content = f.read()

        # Replace packetbeat architecture
        content = content.replace(
            "packetbeat-9.0.0-linux-arm64", f"packetbeat-9.0.0-linux-{arch}"
        )
        content = content.replace(
            "filebeat-9.0.0-linux-arm64", f"filebeat-9.0.0-linux-{arch}"
        )

        with open(temp_dockerfile, "w") as f:
            f.write(content)

        print(f"[*] Building image: {tag} for architecture: {arch}")
        subprocess.run(
            ["docker", "build", "-t", tag, path, "-f", temp_dockerfile], check=True
        )
        return True
    except Exception as e:
        print(f"[!] Error building image: {str(e)}")
        return False
    finally:
        # Clean up temporary file
        if os.path.exists(temp_dockerfile):
            os.remove(temp_dockerfile)


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
    print("3. Default (Nginx + noVNC Kali)")
    print("4. All")

    choice = input("Enter your choice (1/2/3/4): ").strip()

    selected_dirs = []
    if choice == "1":
        selected_dirs = [("targeted", BASE_DIRS["Targeted"])]
    elif choice == "2":
        selected_dirs = [("attacker", BASE_DIRS["Attacker"])]
    elif choice == "3":
        # Use default Nginx and noVNC Kali
        print("[*] Building default images (Nginx + noVNC Kali)...")
        success = True
        for prefix, path in DEFAULT_BUILDS.items():
            if not build_image(path, prefix):
                success = False
                print(f"[!] Failed to build {prefix} image")
        if not success:
            print("[!] Some images failed to build, please check error messages")
        return
    elif choice == "4":
        selected_dirs = [
            ("targeted", BASE_DIRS["Targeted"]),
            ("attacker", BASE_DIRS["Attacker"]),
        ]
    else:
        print("[!] Invalid choice.")
        return

    success = True
    for prefix, path in selected_dirs:
        docker_paths = find_docker_builds(path)
        if not docker_paths:
            print(f"[!] No Dockerfiles found in {path}")
            continue
        selected = select_path(docker_paths)
        if selected and not build_image(selected, prefix):
            success = False
            print(f"[!] Failed to build {prefix} image")

    if not success:
        print("[!] Some images failed to build, please check error messages")


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
