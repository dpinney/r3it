# R3it install script

import sys, os, platform

from r3it.defaults import r3itDir
sys.path.insert(0, r3itDir)

import config

os.system("cd " + r3itDir)
os.system("sudo pip3 install -r requirements.txt")

if platform.system() == "Linux":
    os.system("sudo apt-get update -y -q")
    os.system("sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q")
    os.system("sudo apt-get install letsencrypt python3-pip authbind -y -q")

# provision TLS
    os.system("sudo certbot certonly --standalone --agree-tos -n -m " + config.r3itEmailAddress + " -d " + config.DOMAIN)

# install certs
    os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/fullchain.pem " + r3itDir)
    os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/privkey.pem " + r3itDir)
    os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/cert.pem " + r3itDir)
    os.system("sudo ln -s /etc/letsencrypt/live/" + config.DOMAIN + "/chain.pem " + r3itDir)

# install systemd unit files for r3it and certificate renewal.
    os.system("sudo ln -s " + r3itDir + "r3it.service /etc/systemd/system/r3it.service")
    os.system("sudo ln -s " + r3itDir + "cert.service /etc/systemd/system/")
    os.system("sudo ln -s " + r3itDir + "cert.timer /etc/systemd/system/")

# create log file
    os.system("sudo mkdir " + r3itDir + "data")
    os.system("sudo touch " + r3itDir + "data/log")

# create directory for LetsEncrypt acme challenges.
    os.system("sudo mkdir -p " + r3itDir + ".well-known/acme-challenge")

# Add r3it user:group
    os.system("sudo useradd -r r3it")
    os.system("sudo chown -R r3it:r3it " + r3itDir + "..")
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
