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

# DNS

# provision TLS

certbot certonly --agree-tos -m georgewalkeriv@gmail.com -d jce.r3it.ghw.io

# install service

ln -s ~/r3it/r3it/r3it.service /etc/systemd/system/r3it.service

# enable service

systemctl enable r3it

# cron jobs
