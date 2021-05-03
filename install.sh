#!/bin/bash

# Check for root. NB: seems like actually a bad idea b/c sudo doesn't maintain home dir of user.

# if [[ $EUID > 0 ]]
#   then echo "Please run as root"
#   exit
# fi

# Get email address and domain.

read -p "Enter the admin's email address:" email
read -p "Enter the domain name:" domain

# R3it install script

sudo apt-get update -y -q
sudo apt-get upgrade -y -q

# install python3.6, pip, letsencrypt

sudo apt-get install letsencrypt -y -q

# install omf
# cd ~/
# git clone https://github.com/dpinney/omf.git
# cd ~/omf
# sudo python3.6 ~/omf/install.py

# install requirements
cd ~/r3it
pip install -r requirements.txt

# provision TLS

sudo certbot certonly --standalone --agree-tos -n -m $email -d $domain

# install certs

sudo --preserve-env=HOME ln -s /etc/letsencrypt/live/$domain/fullchain.pem ~/r3it/r3it/
sudo --preserve-env=HOME ln -s /etc/letsencrypt/live/$domain/privkey.pem ~/r3it/r3it/
sudo --preserve-env=HOME ln -s /etc/letsencrypt/live/$domain/cert.pem ~/r3it/r3it/
sudo --preserve-env=HOME ln -s /etc/letsencrypt/live/$domain/chain.pem ~/r3it/r3it/

# install systemd unit files for r3it and certificate renewal.

sudo --preserve-env=HOME ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service
sudo --preserve-env=HOME ln -s ~/r3it/r3it/cert.{s..t}* /etc/systemd/system/

# create log file

mkdir ~/r3it/r3it/data
touch ~/r3it/r3it/data/log

# create local config file
echo 'from defaults import *' > ~/r3it/r3it/config.py

# enable r3it

sudo systemctl enable /etc/systemd/system/r3it.service
sudo systemctl start r3it
sudo systemctl enable /etc/systemd/system/cert.service
sudo systemctl enable /etc/systemd/system/cert.timer
# sudo systemctl start cert.timer