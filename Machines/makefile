.PHONY: install stop reinstall remove
install:#build images
	docker build -t targeter . -f=./Targeter/httpd
	docker build -t attacker . -f=./Attacker/kali-xrdp
	docker-compose up -d
	docker exec `docker ps -aqf "name=targeter"` "make"
stop:#stop the containers
	docker-compose  stop
remove:#remove the containers
	docker-compose  down -v
