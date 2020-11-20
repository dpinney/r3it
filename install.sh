# R3it install script

sudo apt-get update
sudo apt-get upgrade

# install python3.8, pip, gunicorn, cron

sudo apt-get install python3.6 letsencrypt

# install omf
git clone https://github.com/dpinney/omf.git
cd omf
sudo python3 install.py

# download repo
cd ..
git clone https://github.com/dpinney/r3it

 # install requirements
cd r3it
pip3 install -r requirements.txt

# provision TLS

sudo certbot certonly --agree-tos -m EMAIL -d DOMAIN

# install service

ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service

# enable service

sudo systemctl enable r3it

# cron jobs
