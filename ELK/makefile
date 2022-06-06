.PHONY: install start stop check apikey remove
kibanaip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-elk_kibana_1`
install: #downlaod & setting ELK
	git clone https://github.com/deviantony/docker-elk.git
	cd docker-elk && docker-compose up -d &&\
	echo server.publicBaseUrl: "http://$(kibanaip):5601" >> kibana/config/kibana.yml && \
	docker-compose up -d
start:
	cd docker-elk && docker-compose up -d
stop:
	cd docker-elk && docker-compose down
check:
	curl http://elasticsearch:9200 -u elastic:changeme
apikey:
	cd docker-elk && \
	docker-compose exec kibana bin/kibana-encryption-keys generate | tail -4 | tee kibana/config/kibana.yml 
	docker restart docker-elk_kibana
remove:
	cd docker-elk && docker-compose down -v
