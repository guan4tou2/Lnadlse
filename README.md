# Lightweight-network-attack-and-defense-learning-simulation-environment

OS:Linux

1. OS environment
```bash
sudo apt update 
sudo apt install git vim make docker-ce docker-ce-cli containerd.io docker-compose-plugin python3
sudo usermod -aG docker ${USER}
```

2. install
  - Clone project
```bash
git clone https://github.com/guan4tou2/Lnadlse.git
cd Lnadlse
```
  - Data-process-module install
```bash
cd ELK
make
```
After above command,you can use `make check` to check is elasticsearch successful install and running. </br>
If your kibana get error,it may be server.publicBaseUrl,you can try replace url elasticsearch to your ELK host ip. And restart it `docker restart docker-elk_kibana`.</br>
If you need api key,you can use `make apikey` to set it. </br>

  - Attack-and-Defense-module install
```bash
cd Machines
make
```
It will build attack-and-defense-environment by default.Attacker is **kali(GUI)**,Targeter is **httpd** with packetbeat. </br>
You can change machines by make.py. Use `python3 make.py -h` to see what machines can used.

 - aider-module install
```bash
docker pull portainer/portainer
docker run -d -p 9000:9000 --restart=always --name portainer -v /var/run/docker.sock:/var/run/docker.sock portainer/portainer
```
[Portainer](https://github.com/portainer/portainer) can help you to manage your docker container. </br>
It's not necessarily to install,but recommand.

3. Useage



4. Remove
  - Data-process-module
```bash
cd ELK
make remove
```
  - Attack-and-Defense-module 
```bash
cd Machines
make remove
```
 - aider-module
```bash
docker stop portainer
```
