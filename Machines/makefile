.PHONY: install stop remove
install:#build images
	docker build -t targeter . -f=./Targeter/httpd
	chmod 755 ./start.sh
	docker build -t attacker . -f=./Attacker/kali
	docker-compose -f ./docker-compose.yml up -d
stop:#stop the containers
	docker-compose -f ./docker-compose.yml stop
remove:#remove the containers
	docker-compose -f ./docker-compose.yml down -v
