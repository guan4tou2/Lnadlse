.PHONY: install stop remove
install:#build images
	docker build -t targeter . -f=./Targeter/httpd
	docker build -t attacker . -f=./Attacker/kali
	docker-compose up -d
	#docker exec `docker ps -aqf "name=targeter"` "make"
	#docker exec `docker ps -aqf "name=attacker"` ""
stop:#stop the containers
	docker-compose  stop
remove:#remove the containers
	docker-compose  down -v
