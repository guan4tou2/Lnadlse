.PHONY: install check apikey remove
install: #downlaod & setting ELK
	git clone https://github.com/deviantony/docker-elk.git
	cd docker-elk && \
	echo 'server.publicBaseUrl: "http://elasticsearch:5601"' >> kibana/config/kibana.yml && \
	docker-compose docker-compose.yml up -d
check:
	curl http://localhost:9200 -u elastic:changeme
apikey:
	docker-compose exec kibana bin/kibana-encryption-keys generate | tail -4 | tee kibana/config/kibana.yml
	docker restart docker-elk_kibana
remove:
	docker-compose down -v
