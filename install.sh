#!/bin/bash

# Check for root.

if [[ $EUID > 0 ]]
  then echo "Please run as root"
  exit
fi

# Get email address and domain.

read -p "Enter the admin's email address:" email
read -p "Enter the domain name:" domain

# R3it install script

apt-get update
apt-get upgrade

# install python3.8, pip, gunicorn, cron

apt-get install python3.6 letsencrypt python3-pip

# install omf
cd ~/
git clone https://github.com/dpinney/omf.git
cd omf
python3 install.py

# install requirements
cd r3it
pip3 install -r requirements.txt

# provision TLS

certbot certonly --agree-tos -n -m $email -d $domain

# install certs

ln -s /etc/letsencrypt/live/$domain/*.pem ~/r3it/r3it/

# install systemd unit files for r3it and certificate renewal.

ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service
ln -s ~/r3it/r3it/cert.{s..t}* /etc/systemd/system/

# enable r3it

systemctl {enable,start} /etc/systemd/systen/r3it.service
systemctl {enable,start} /etc/systemd/systen/cert.timer
systemctl enable /etc/systemd/systen/cert.service