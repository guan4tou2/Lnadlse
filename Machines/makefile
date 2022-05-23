.PHONY: install start stop remove
KALI_USER=kali
KALI_PASSWORD=kali
install:#build images
	sed -i "s/kibanaip/`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-elk_kibana_1`/g" Beat/packetbeat
	docker build -t targeter_httpd . -f=./Targeter/httpd
	sed -i 's/ARG KALI_USER=kali/ARG KALI_USER=$(KALI_USER)/g' Attacker/kali-xrdp
	sed -i 's/ARG KALI_PASSWORD=kali@123/ARG KALI_PASSWORD=$(KALI_PASSWORD)/g' Attacker/kali-xrdp
	docker build -t attacker_kali-xrdp . -f=./Attacker/kali-xrdp
	docker-compose up -d
	docker exec `docker ps -aqf "name=targeter"` "make"
start:
	docker-compose up -d
stop:#stop the containers
	docker-compose  stop
remove:#remove the containers
	docker-compose  down -v
