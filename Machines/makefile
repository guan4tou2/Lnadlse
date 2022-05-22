.PHONY: install stop setbeat remove
install:#build images
	sed -i "s/kibanaip/`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-elk_kibana_1`/g" Beat/packetbeat
	docker build -t targeter . -f=./Targeter/httpd
	docker build -t attacker . -f=./Attacker/kali-xrdp
	docker-compose up -d
setbeat:
	docker exec `docker ps -aqf "name=targeter"` "make"
stop:#stop the containers
	docker-compose  stop
remove:#remove the containers
	docker-compose  down -v
