.PHONY: install start stop check remove show
kibanaip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elk-kibana-1`
esip=`docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elk-es01-1`
elastic_version=9.0.0
elastic_password=`grep ELASTIC_PASSWORD .env | cut -d '=' -f2`

install: #setup ELK with existing files
	@echo "Setting up ELK stack..."
	@sed -i '' "s/STACK_VERSION=.*/STACK_VERSION=$(elastic_version)/g" .env
	@if ! docker network ls | grep -q elk_net; then \
		docker network create elk_net; \
	fi
	docker-compose build

show:
	@echo "Kibana IP: $(kibanaip)"
	@echo "Elasticsearch IP: $(esip)"

start:
	docker-compose up -d
	@echo "Waiting for services to initialize..."
	@sleep 30
	@make show
	@make check

stop:
	docker-compose down

check:
	@echo "Checking Elasticsearch connection..."
	@curl -s -k https://localhost:9200 -u elastic:$(elastic_password) || echo "Connection failed"

remove:
	docker-compose down -v
