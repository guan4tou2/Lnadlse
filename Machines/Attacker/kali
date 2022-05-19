FROM kalilinux/kali-rolling

ARG KALI_USER 
ARG KALI_PASSWORD
env KALI_USER=${KALI_USER} \
    KALI_PASSWORD=${KALI_PASSWORD}

RUN apt-get -y update && apt-get -y upgrade && \
   DEBIAN_FRONTEND=noninteractive apt-get install -y \
   pciutils apt-utils\
   bash-completion && \
   apt-get autoremove -y && \
   apt-get clean

RUN printf "alias ll='ls $LS_OPTIONS -l'\nalias l='ls $LS_OPTIONS -lA'\n\n# enable bash completion in interactive shells\nif [ -f /etc/bash_completion ] && ! shopt -oq posix; then\n    . /etc/bash_completion\nfi\n" > /root/.bashrc
RUN mkdir /data
#ADD setup.sh /setup.sh
#RUN chmod 755 /setup.sh

RUN apt-get -y install xorg xrdp iputils-ping 
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install kali-linux-large kali-desktop-xfce
RUN useradd -ms /bin/bash $KALI_USER
RUN echo "$KALI_USER:$KALI_PASSWORD" | chpasswd
RUN echo "$KALI_USER ALL=(ALL:ALL) ALL" >> /etc/sudoers

EXPOSE 3389
VOLUME /data /root /home/$KALI_USER
ENTRYPOINT /etc/init.d/xrdp start && tail -F /var/log/xrdp-kali.log
