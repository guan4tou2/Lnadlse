FROM kalilinux/kali-rolling

# 設定變數
ARG KALI_USER=kali
ARG KALI_PASSWORD=kali
ENV KALI_USER=${KALI_USER} \
    KALI_PASSWORD=${KALI_PASSWORD}

# 更新與安裝必要工具
RUN apt update && apt -y upgrade && \
    DEBIAN_FRONTEND=noninteractive apt install -y \
    # kali-linux-core \
    # kali-linux-default \
    pciutils \
    bash-completion \
    apt-utils \
    sudo \
    openssh-server \
    x11-xserver-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*


# 安裝 locales 並產生 en_US.UTF-8 語系
RUN apt update && apt install -y locales && \
    sed -i 's/^# *\(en_US.UTF-8\)/\1/' /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8

# 環境變數設定
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# 建立 SSH 相關目錄
RUN mkdir -p /var/run/sshd

# 配置 SSH
RUN echo "Port 22" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "X11Forwarding yes" >> /etc/ssh/sshd_config && \
    echo "X11UseLocalhost no" >> /etc/ssh/sshd_config

# 建立使用者
RUN useradd -ms /bin/bash $KALI_USER && \
    echo "$KALI_USER:$KALI_PASSWORD" | chpasswd && \
    echo "$KALI_USER ALL=(ALL:ALL) ALL" >> /etc/sudoers

# 建立資料夾
RUN mkdir /data

# 建立啟動腳本
RUN echo '#!/bin/bash\n\
    export DISPLAY=host.docker.internal:0.0\n\
    /usr/sbin/sshd -D' > /start.sh && \
    chmod +x /start.sh

# 開放 port 與掛載目錄
EXPOSE 22
VOLUME ["/data", "/root", "/home/$KALI_USER"]

# 預設執行 sshd，保持容器常駐
CMD ["/bin/bash", "/start.sh"]
