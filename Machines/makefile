.PHONY: install stop remove
install:#build images
	docker build -t targeter . -f=./Targeter/httpd
	chmod 755 ./start.sh
	docker build -t attacker . -f=./Attacker/kali
	docker-compose  up -d
	#docker exec target makefile
stop:#stop the containers
	docker-compose  stop
remove:#remove the containers
	docker-compose  down -v
