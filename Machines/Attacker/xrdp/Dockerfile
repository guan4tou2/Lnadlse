FROM kalilinux/kali-rolling

ARG KALI_USER=kali
ARG KALI_PASSWORD=kali
env KALI_USER=${KALI_USER} \
    KALI_PASSWORD=${KALI_PASSWORD}

RUN apt update && apt -y upgrade &&  DEBIAN_FRONTEND=noninteractive \
    apt install -y pciutils apt-utils bash-completion openssh-server && \
    apt-get autoremove -y && \
    apt-get clean

RUN echo "Port 22" >> /etc/ssh/sshd_config
RUN echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "X11Forwarding yes" >> /etc/ssh/sshd_config
RUN echo "X11UseLocalhost no" >> /etc/ssh/sshd_config

RUN printf "alias ll='ls $LS_OPTIONS -l'\nalias l='ls $LS_OPTIONS -lA'\n\n# enable bash completion in interactive shells\nif [ -f /etc/bash_completion ] && ! shopt -oq posix; then\n    . /etc/bash_completion\nfi\n" > /root/.bashrc
RUN mkdir /data

RUN apt -y install xorg xrdp iputils-ping 
RUN DEBIAN_FRONTEND=noninteractive apt -y install kali-desktop-xfce
RUN useradd -ms /bin/bash $KALI_USER
RUN echo "$KALI_USER:$KALI_PASSWORD" | chpasswd
RUN echo "$KALI_USER ALL=(ALL:ALL) ALL" >> /etc/sudoers

EXPOSE 3389
EXPOSE 22
VOLUME /data /root /home/$KALI_USER
ENTRYPOINT /etc/init.d/xrdp start && tail -F /var/log/xrdp-kali.log
