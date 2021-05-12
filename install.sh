#!/bin/bash

# R3it install script

# Check for root. NB: seems like actually a bad idea b/c sudo doesn't maintain home dir of user.

# if [[ $EUID > 0 ]]
#   then echo "Please run as root"
#   exit
# fi

# Get email address and domain.

read -p "Enter the admin's email address:" email
read -p "Enter the domain name:" domain

sudo apt-get update -y -q
sudo apt-get upgrade -y -q

# install pip, letsencrypt

sudo apt-get install letsencrypt python3-pip authbind -y -q

# install omf
# cd /opt/
# git clone https://github.com/dpinney/omf.git
# cd /opt/omf
# sudo python3.6 /opt/omf/install.py

# install requirements
sudo useradd -r r3it
sudo chown -R r3it:r3it /opt/r3it
cd /opt/r3it
sudo pip3 install -r requirements.txt

# provision TLS

sudo certbot certonly --standalone --agree-tos -n -m $email -d $domain

# install certs

sudo ln -s /etc/letsencrypt/live/$domain/fullchain.pem /opt/r3it/r3it/
sudo ln -s /etc/letsencrypt/live/$domain/privkey.pem /opt/r3it/r3it/
sudo ln -s /etc/letsencrypt/live/$domain/cert.pem /opt/r3it/r3it/
sudo ln -s /etc/letsencrypt/live/$domain/chain.pem /opt/r3it/r3it/

# install systemd unit files for r3it and certificate renewal.

sudo ln -s /opt/r3it/r3it/r3it.service /etc/systemd/system/r3it.service
sudo ln -s /opt/r3it/r3it/cert.{s..t}* /etc/systemd/system/

# create log file

sudo mkdir /opt/r3it/r3it/data
sudo touch /opt/r3it/r3it/data/log

# create directory for LetsEncrypt acme challenges.

sudo mkdir -p /opt/r3it/r3it/.well-known/acme-challenge

# configure authbind so r3it can bind to low-numbered ports sans root.

sudo touch /etc/authbind/byport/{80,443}
sudo chown r3it:r3it /etc/authbind/byport/{80,443}
sudo chmod 710 /etc/authbind/byport/{80,443}

# create local config file
# echo 'from defaults import *' > /opt/r3it/r3it/config.py

# enable r3it

sudo systemctl enable /etc/systemd/system/r3it.service
sudo systemctl start r3it
sudo systemctl enable /etc/systemd/system/cert.service
sudo systemctl enable /etc/systemd/system/cert.timer
# sudo systemctl start cert.timer