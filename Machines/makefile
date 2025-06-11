.PHONY: install start stop remove
KALI_USER=kali
KALI_PASSWORD=kali

install:#build images
	@if ! docker network ls | grep -q elk_net; then \
		docker network create elk_net; \
	fi
	docker build -t targeted_nginx ./Targeted -f=./Targeted/nginx
	docker build -t attacker_kali-novnc ./Attacker -f=./Attacker/kali-novnc
	
start:
	docker-compose up -d

stop:#stop the containers
	docker-compose stop

remove:#remove the containers
	docker-compose down -v


