.PHONY: install check apikey restart remove
install: #downlaod & setting ELK
	git clone https://github.com/deviantony/docker-elk.git
	cd docker-elk && docker-compose docker-compose.yml up -d
check:
	curl http://localhost:9200 -u elastic:changeme
apikey:
	docker-compose exec kibana bin/kibana-encryption-keys generate | tail -4 | cat >> kibana/config/kibana.yml
restart:
	docker restart docker-elk_kibana
remove:
  docker-compose dwon -v
