.PHONY:beat
beat:
	apt update 
	apt upgrade -y
	apt install -y curl ca-certificates vim
	curl -L -O https://artifacts.elastic.co/downloads/beats/packetbeat/packetbeat-8.2.0-linux-x86_64.tar.gz
	tar xzvf packetbeat-8.*-linux-x86_64.tar.gz
	cd ./packetbeat-8.*-linux-x86_64 && \
		sed -i 's/#setup.dashboards.enabled: false/setup.dashboards.enabled: true\nsetup.template.overwrite: false/g' packetbeat.yml && \
		sed -i 's/hosts: \["localhost:9200"\]/hosts: \["elasticsearch:9200"\]/g' packetbeat.yml && \
		sed -i 's/#username: "elastic"/username: "elastic"/g' packetbeat.yml && \
		sed -i 's/#password: "changeme"/password: "changeme"/g' packetbeat.yml && \
		sed -i 's/#host: "localhost:5601"/host: "elasticsearch:5601"\n  username: "elastic"\n  password: "changeme"/g' packetbeat.yml 
	cd ./packetbeat-8.*-linux-x86_64 && ./packetbeat setup -e
	cd ./packetbeat-8.*-linux-x86_64 && chown root packetbeat.yml 
	cd ./packetbeat-8.*-linux-x86_64 && ./packetbeat -e
