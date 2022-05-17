# Lightweight-network-attack-and-defense-learning-simulation-environment
OS:Linux

1. OS environment
```bash
sudo apt update 
sudo apt install git vim make docker-ce docker-ce-cli containerd.io docker-compose-plugin python3
sudo usermod -aG docker ${USER}
```

2. install
- Clone project.
```bash
git clone https://github.com/guan4tou2/Lnadlse.git
cd Lnadlse
```

- Data-process-module install
```bash
cd ELK
make
```
After above command,you can use `make check` to check is elasticsearch successful install and running.

- Attack-and-Defense-module install
```bash
cd Machines
make
```
It will build attack-and-defense-environment by default.Attacker is **kali(GUI)**,Targeter is **httpd** with packetbeat. </br>
You can change machines by make.py. Use `python3 make.py -h` to see what machines can used.

3. aider-module
```bash
docker pull portainer/portainer
docker run -d -p 9000:9000 --restart=always --name portainer -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer
```
[Office document](https://github.com/portainer/portainer)
