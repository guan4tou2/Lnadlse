.PHONY: install start stop check apikey remove show
kibanaip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-elk_kibana_1`
esip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' docker-elk_elasticsearch_1`
install: #downlaod & setting ELK
	if test -d docker-elk;then echo "exist";elst git clone https://github.com/deviantony/docker-elk.git;fi;
	cd docker-elk &&\
	sed -i "s/ELASTIC_VERSION=.\..\../ELASTIC_VERSION=8.1.0/g" .env && \
	docker-compose up -d &&\
	sed -i "s/elasticsearch:9200/$(esip):9200/g" kibana/config/kibana.yml && \
	echo server.publicBaseUrl: "http://$(kibanaip):5601" >> kibana/config/kibana.yml && \
	docker-compose up -d
	@make show
	@make check
show:
	@echo kibana ip is $(kibanaip)
	@echo es ip is $(esip)
start:
	cd docker-elk && docker-compose up -d
stop:
	cd docker-elk && docker-compose down
check:
	curl http://$(esip):9200 -u elastic:changeme
apikey:
	cd docker-elk && \
	docker-compose exec kibana bin/kibana-encryption-keys generate | tail -4 | tee kibana/config/kibana.yml 
	docker restart docker-elk_kibana
remove:
	cd docker-elk && docker-compose down -v
