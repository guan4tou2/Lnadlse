# Lightweight-network-attack-and-defense-learning-simulation-environment
# [輕便化之網路攻防學習模擬環境](README_ch.md)

A Docker-based network security simulation environment that includes ELK stack for log analysis and attack simulation environment.

## System Requirements

- Docker
- Docker Compose
- Python 3.8+
- Make

## Running Environment

### ELK Stack
- Elasticsearch: 9.0.0
- Logstash: 9.0.0
- Kibana: 9.0.0

### Target Machines
- Nginx: latest
- Httpd: latest

### Attacker Machines
- Kali Linux: latest
  - noVNC: Web-based VNC client
  - Xrdp: Remote Desktop Protocol
  - X11: X Window System

## Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>
```

2. Install ELK environment:
```bash
cd ELK
python make.py install
```

3. Install simulation environment:
```bash
cd Machines
python make.py install
```
During installation, you need to select what to build:
- 1: Build target machines only (Targeted)
- 2: Build attacker machines only (Attacker)
- 3: Build default machines (Nginx + noVNC Kali)
- 4: Build all machines

Then select specific machine types to build.

1. Install Python dependencies:
```bash
cd Web
pip install -r requirements.txt
```

## Running Instructions

1. Start the Web interface:
```bash
cd Web
python app.py
```

2. Access the Web interface:
- Open your browser and visit `http://localhost:5000`

3. Usage Guide:
- Click "Start ELK Stack" to start the ELK environment
- Select target machine type (Nginx/Httpd) and attacker machine type (Kali)
- Click "Start Simulation" to start the simulation environment
- Use "Stop Simulation" to stop the simulation environment
- Use "Stop ELK" to stop the ELK environment

## Features

### ELK Environment
- Elasticsearch: For storing and retrieving log data
- Logstash: For log collection and processing
- Kibana: For log visualization and analysis

### Simulation Environment
- Target Machines:
  - Nginx: Web server
  - Httpd: Web server
- Attacker Machines:
  - Kali Linux: Penetration testing system
  - Multiple remote access methods supported (noVNC/Xrdp/X11)

## Management Commands

In the Machines directory, you can use the following commands to manage the simulation environment:

```bash
# Start all containers
python make.py start

# Stop all containers
python make.py stop

# Remove all containers and volumes
python make.py remove
```

## Important Notes

1. First-time ELK environment startup may take a while, please be patient
2. Ensure your system has enough memory to run the ELK environment (recommended at least 4GB)
3. If you encounter permission issues, make sure the Docker service is running
4. When stopping services, use the corresponding stop buttons to avoid directly closing containers
5. When installing the simulation environment, ensure all required Docker images are built

## Troubleshooting

1. If the ELK environment fails to start:
   - Check if your system has enough memory
   - Verify that the Docker service is running properly
   - Check Docker logs for detailed information

2. If the simulation environment fails to start:
   - Ensure the ELK environment is running properly
   - Check Docker network configuration
   - Verify that all required Docker images are built correctly
   - Check container logs for detailed information

## Contributing

Issues and Pull Requests are welcome to help improve the project.

## License

[Add license information] 