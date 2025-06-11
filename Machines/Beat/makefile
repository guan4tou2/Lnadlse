.PHONY: beat
version=9.0.0
arch=linux-arm64

beat:
	apt update 
	apt upgrade -y
	apt install -y curl ca-certificates vim
	curl -L -O https://artifacts.elastic.co/downloads/beats/packetbeat/packetbeat-$(version)-$(arch).tar.gz
	tar xzvf packetbeat-$(version)-$(arch).tar.gz
	cd ./packetbeat-$(version)-$(arch) && \
		sed -i '/^output.elasticsearch:/a \  ssl.verification_mode: none' packetbeat.yml && \
		sed -i 's/#setup.dashboards.enabled: false/setup.dashboards.enabled: true\nsetup.template.overwrite: false/g' packetbeat.yml && \
		sed -i 's/hosts: \["localhost:9200"\]/hosts: \["https:\/\/es01:9200"\]/g' packetbeat.yml && \
		sed -i 's/#username: "elastic"/username: "elastic"/g' packetbeat.yml && \
		sed -i 's/#password: "changeme"/password: "changeme"/g' packetbeat.yml && \
		sed -i 's/#host: "localhost:5601"/host: "kibana:5601"\n  username: "elastic"\n  password: "changeme"/g' packetbeat.yml 
	cd ./packetbeat-$(version)-$(arch) && ./packetbeat setup -e && chown root packetbeat.yml && ./packetbeat test config &

	# 使用 printf 创建 systemd service 文件
	printf "[Unit]\nDescription=Packetbeat\nAfter=network.target\n\n[Service]\nExecStart=/root/packetbeat-$(version)-$(arch)/packetbeat -e\nWorkingDirectory=/root/packetbeat-$(version)-$(arch)\nRestart=always\nUser=root\n\n[Install]\nWantedBy=multi-user.target\n" > /etc/systemd/system/packetbeat.service

	# 重新加载 systemd 配置
	systemctl daemon-reload

	# 启用并启动 packetbeat 服务
	systemctl enable packetbeat
	systemctl start packetbeat

	# 检查服务状态
	systemctl status packetbeat
