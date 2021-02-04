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

apt-get install python3.6 letsencrypt

# install omf
git clone https://github.com/dpinney/omf.git
cd omf
python3 install.py

# download repo
cd ..
git clone https://github.com/dpinney/r3it

# install requirements
cd r3it
pip3 install -r requirements.txt

# provision TLS

certbot certonly --agree-tos -n -m $email -d $domain

# install service

ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service

# install certs

ln -s /etc/letsencrypt/live/$domain/fullchain.pem ~/r3it/r3it/fullchain.pem
ln -s /etc/letsencrypt/live/$domain/privkey.pem ~/r3it/r3it/privkey.pem
ln -s /etc/letsencrypt/live/$domain/cert.pem ~/r3it/r3it/cert.pem

# enable service

systemctl enable r3it

# cron jobs
