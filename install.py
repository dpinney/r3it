# R3it install script

import sys, os

sys.path.insert(0, '/opt/r3it/r3it')

from r3it import config

os.system("sudo apt-get update -y -q")
os.system("sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q")

os.system("sudo apt-get install letsencrypt python3-pip authbind -y -q")

# install requirements
os.system("cd /opt/r3it")
os.system("sudo pip3 install -r requirements.txt")

# provision TLS
os.system("sudo certbot certonly --standalone --agree-tos -n -m " + config.r3itEmailAddress + " -d " + config.DOMAIN)

# install certs
os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/fullchain.pem /opt/r3it/r3it/")
os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/privkey.pem /opt/r3it/r3it/")
os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/cert.pem /opt/r3it/r3it/")
os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/chain.pem /opt/r3it/r3it/")

# install systemd unit files for r3it and certificate renewal.
os.system("sudo ln -s /opt/r3it/r3it/r3it.service /etc/systemd/system/r3it.service")
os.system("sudo ln -s /opt/r3it/r3it/cert.service /etc/systemd/system/")
os.system("sudo ln -s /opt/r3it/r3it/cert.timer /etc/systemd/system/")

# create log file
os.system("sudo mkdir /opt/r3it/r3it/data")
os.system("sudo touch /opt/r3it/r3it/data/log")

# create directory for LetsEncrypt acme challenges.
os.system("sudo mkdir -p /opt/r3it/r3it/.well-known/acme-challenge")

# Add r3it user:group
os.system("sudo useradd -r r3it")
os.system("sudo chown -R r3it:r3it /opt/r3it")
os.system("sudo chown -R r3it:r3it /etc/letsencrypt")

# configure authbind so r3it can bind to low-numbered ports sans root.
os.system("sudo touch /etc/authbind/byport/80")
os.system("sudo touch /etc/authbind/byport/443")
os.system("sudo chown r3it:r3it /etc/authbind/byport/80")
os.system("sudo chown r3it:r3it /etc/authbind/byport/443")
os.system("sudo chmod 710 /etc/authbind/byport/80")
os.system("sudo chmod 710 /etc/authbind/byport/443")

# enable r3it
os.system("sudo systemctl enable /etc/systemd/system/r3it.service")
os.system("sudo systemctl start r3it")
os.system("sudo systemctl enable /etc/systemd/system/cert.service")
os.system("sudo systemctl enable /etc/systemd/system/cert.timer")