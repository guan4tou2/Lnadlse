FROM httpd:latest
MAINTAINER weichen

# 安裝需要的套件
RUN apt update && apt upgrade -y && \
    apt install -y curl ca-certificates vim supervisor

# 設定台灣鏡像
RUN sed -i 's|http://deb.debian.org|http://mirror.twds.com.tw|g' /etc/apt/sources.list.d/debian.sources || true

# 安裝 Packetbeat
WORKDIR /opt
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/packetbeat/packetbeat-9.0.0-linux-arm64.tar.gz && \
    tar xzvf packetbeat-9.0.0-linux-arm64.tar.gz && \
    mv packetbeat-9.0.0-linux-arm64 /opt/packetbeat && \
    cp /opt/packetbeat/packetbeat.yml /opt/packetbeat/packetbeat.yml.bak

# 修改 Packetbeat 設定
RUN sed -i '/^output.elasticsearch:/a \  ssl.verification_mode: none' /opt/packetbeat/packetbeat.yml && \
    sed -i 's/#setup.dashboards.enabled: false/setup.dashboards.enabled: true\nsetup.template.overwrite: false/g' /opt/packetbeat/packetbeat.yml && \
    sed -i 's/hosts: \["localhost:9200"\]/hosts: \["https:\/\/es01:9200"\]/g' /opt/packetbeat/packetbeat.yml && \
    sed -i 's/#username: "elastic"/username: "elastic"/g' /opt/packetbeat/packetbeat.yml && \
    sed -i 's/#password: "changeme"/password: "changeme"/g' /opt/packetbeat/packetbeat.yml && \
    sed -i 's/#host: "localhost:5601"/host: "kibana:5601"\n  username: "elastic"\n  password: "changeme"/g' /opt/packetbeat/packetbeat.yml

# 安裝 Filebeat
WORKDIR /opt
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-9.0.0-linux-arm64.tar.gz && \
    tar xzvf filebeat-9.0.0-linux-arm64.tar.gz && \
    mv filebeat-9.0.0-linux-arm64 /opt/filebeat && \
    cp /opt/filebeat/filebeat.yml /opt/filebeat/filebeat.yml.bak

# 修改 Filebeat 設定
RUN sed -i '/^output.elasticsearch:/a \  ssl.verification_mode: none' /opt/filebeat/filebeat.yml && \
    sed -i '/- type: filestream/{n; s/enabled: false/enabled: true/}' /opt/filebeat/filebeat.yml && \
    sed -i 's/#setup.dashboards.enabled: false/setup.dashboards.enabled: true\nsetup.template.overwrite: false/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/hosts: \["localhost:9200"\]/hosts: \["https:\/\/es01:9200"\]/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#username: "elastic"/username: "elastic"/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#password: "changeme"/password: "changeme"/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#host: "localhost:5601"/host: "kibana:5601"\n  username: "elastic"\n  password: "changeme"/g' /opt/filebeat/filebeat.yml

# 建立 Apache 日誌檔案（如果不存在）
RUN touch /usr/local/apache2/logs/access_log /usr/local/apache2/logs/error_log

# 啟用 Filebeat 對 Apache 日誌的監控（自定義）
RUN echo "- type: log\n  enabled: true\n  paths:\n    - /usr/local/apache2/logs/access_log\n    - /usr/local/apache2/logs/error_log" >> /opt/filebeat/filebeat.yml

# Supervisor config
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80
CMD ["/usr/bin/supervisord", "-n"]
