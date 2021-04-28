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

# install python3.8, pip, gunicorn, cron

sudo apt-get install python3.6 letsencrypt python3-pip -y -q

# install omf
cd ~/
git clone https://github.com/dpinney/omf.git
cd ~/omf
sudo python3.6 ~/omf/install.py

# install requirements
cd ~/r3it
pip3 install -r requirements.txt

# provision TLS

sudo certbot certonly --standalone --agree-tos -n -m $email -d $domain

# install certs

sudo --preserve-env=HOME ln -s /etc/letsencrypt/live/$domain/*.pem ~/r3it/r3it/

# install systemd unit files for r3it and certificate renewal.

sudo --preserve-env=HOME ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service
sudo --preserve-env=HOME ln -s ~/r3it/r3it/cert.{s..t}* /etc/systemd/system/

# create log file

mkdir ~/r3it/r3it/data
touch ~/r3it/r3it/data/log

# enable r3it

sudo systemctl enable /etc/systemd/system/r3it.service
sudo systemctl start r3it
sudo systemctl enable /etc/systemd/system/cert.timer
sudo systemctl start cert.timer