.PHONY: install start stop remove
KALI_USER=kali
KALI_PASSWORD=kali

install:#build images
	@if ! docker network ls | grep -q elk_net; then \
		docker network create elk_net; \
	fi
	docker build -t targeted_nginx . -f=./Targeted/nginx
	sed -i '' 's/ARG KALI_USER=kali/ARG KALI_USER=$(KALI_USER)/g' Attacker/kali-novnc
	sed -i '' 's/ARG KALI_PASSWORD=kali@123/ARG KALI_PASSWORD=$(KALI_PASSWORD)/g' Attacker/kali-novnc
	docker build -t attacker_kali-novnc ./Attacker -f=./Attacker/kali-novnc
	docker-compose up -d

start:
	docker-compose up -d

stop:#stop the containers
	docker-compose stop

remove:#remove the containers
	docker-compose down -v


