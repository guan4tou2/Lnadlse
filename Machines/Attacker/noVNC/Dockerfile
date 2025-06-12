FROM kalilinux/kali-rolling:latest
LABEL maintainer="admin@csalab.id"

# 設定變數
ARG KALI_USER=kali
ARG KALI_PASSWORD=kali@123
ENV KALI_USER=${KALI_USER} \
    KALI_PASSWORD=${KALI_PASSWORD}

RUN sed -i "s/http.kali.org/mirror.twds.com.tw/g" /etc/apt/sources.list && \
    apt-get update && \
    apt-get -y upgrade
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install \
    sudo \
    dos2unix \
    openssh-server \
    python2 \
    python3-pip \
    python3-virtualenv \
    dialog \
    firefox-esr \
    inetutils-ping \
    net-tools \
    tigervnc-standalone-server \
    tigervnc-xorg-extension \
    tigervnc-viewer \
    novnc \
    dbus-x11 \
    xfce4-goodies \
    kali-desktop-xfce 

# Install kali-linux-headless, kali-linux-core, kali-linux-default
RUN DEBIAN_FRONTEND=noninteractive apt-get -yq install \
    kali-tools-top10 \
    # kali-linux-headless \
    kali-linux-core \
    kali-linux-default

# RUN DEBIAN_FRONTEND=noninteractive apt-get -yq full-upgrade

RUN apt-get -y autoremove && \
    apt-get clean all && \
    rm -rf /var/lib/apt/lists/* && \
    useradd -m -c "Kali Linux" -s /bin/bash -d /home/kali kali && \
    sed -i "s/#ListenAddress 0.0.0.0/ListenAddress 0.0.0.0/g" /etc/ssh/sshd_config && \
    sed -i "s/off/remote/g" /usr/share/novnc/app/ui.js && \
    echo "kali ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    mkdir /run/dbus && \
    # ln -s /usr/bin/python3 /usr/bin/python && \
    touch /usr/share/novnc/index.htm
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
USER kali
WORKDIR /home/kali
RUN mkdir -p /home/kali/.config && \
    virtualenv /home/kali/.config/app && \
    echo "source /home/kali/.config/app/bin/activate" >> /home/kali/.bashrc

RUN dos2unix /entrypoint.sh
ENV PASSWORD=${KALI_PASSWORD}
ENV SHELL=/bin/bash
EXPOSE 8080
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]