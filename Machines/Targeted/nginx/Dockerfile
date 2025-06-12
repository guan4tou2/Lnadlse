FROM nginx:latest
MAINTAINER weichen

# 安裝需要的套件
RUN apt update && apt upgrade -y && \
    apt install -y curl ca-certificates vim supervisor

# 設定台灣鏡像
RUN sed -i 's|http://deb.debian.org|http://mirror.twds.com.tw|g' /etc/apt/sources.list.d/debian.sources 

# 安裝 Packetbeat
WORKDIR /opt
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/packetbeat/packetbeat-9.0.0-linux-replacearch.tar.gz && \
    tar xzvf packetbeat-9.0.0-linux-replacearch.tar.gz && \
    mv packetbeat-9.0.0-linux-replacearch /opt/packetbeat && \
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
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-9.0.0-linux-replacearch.tar.gz && \
    tar xzvf filebeat-9.0.0-linux-replacearch.tar.gz && \
    mv filebeat-9.0.0-linux-replacearch /opt/filebeat && \
    cp /opt/filebeat/filebeat.yml /opt/filebeat/filebeat.yml.bak

# 修改 Filebeat 設定
RUN sed -i '/^output.elasticsearch:/a \  ssl.verification_mode: none' /opt/filebeat/filebeat.yml && \
    sed -i '/- type: filestream/{n; s/enabled: false/enabled: true/}' /opt/filebeat/filebeat.yml && \
    sed -i 's/#setup.dashboards.enabled: false/setup.dashboards.enabled: true\nsetup.template.overwrite: false/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/hosts: \["localhost:9200"\]/hosts: \["https:\/\/es01:9200"\]/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#username: "elastic"/username: "elastic"/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#password: "changeme"/password: "changeme"/g' /opt/filebeat/filebeat.yml && \
    sed -i 's/#host: "localhost:5601"/host: "kibana:5601"\n  username: "elastic"\n  password: "changeme"/g' /opt/filebeat/filebeat.yml

RUN cd /opt/filebeat && ./filebeat modules enable nginx
RUN rm /var/log/nginx/access.log /var/log/nginx/error.log && \
    touch /var/log/nginx/access.log /var/log/nginx/error.log

# 啟用 access.enabled
RUN sed -i '/^\s*access:/,/^\s*[a-z_]*:/s/^\(\s*enabled:\).*/\1 true/' /opt/filebeat/modules.d/nginx.yml
# 設定 access.var.paths
# RUN sed -i '/^\s*access:/,/^\s*[a-z_]*:/s|^\(\s*\)#*var.paths:.*|\1var.paths: ["/var/log/nginx/access.log*"]|' /opt/filebeat/modules.d/nginx.yml
# 啟用 error.enabled
RUN sed -i '/^\s*error:/,/^\s*[a-z_]*:/s/^\(\s*enabled:\).*/\1 true/' /opt/filebeat/modules.d/nginx.yml
# 設定 error.var.paths
# RUN sed -i '/^\s*error:/,/^\s*[a-z_]*:/s|^\(\s*\)#*var.paths:.*|\1var.paths: ["/var/log/nginx/error.log*"]|' /opt/filebeat/modules.d/nginx.yml


# Supervisor config
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80
CMD ["/usr/bin/supervisord", "-n"]
