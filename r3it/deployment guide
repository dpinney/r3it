Deploy:
1. Create an Ubuntu 20.04 VM
2. Configure DNS to point to new VM.
3. Install OMF per <link to omf install guide>
4. git clone https://github.com/dpinney/r3it
5. cd r3it
6. pip install -r requirements.txt
7. Configure let's encrypt <NB: automate this>
8. Edit config.py, put in API keys, domain name, etc. as appropriate.
9. Install r3it.service <how?>
10. Start r3it.service: sudo systemctl start r3it

Update:
1. cd ~/omf
2. git pull
3. cd ~/r3it
4. git pull
5. sudo systemctl stop r3it
6. sudo systemctl start r3it

Issues: 
1. let's encrypt should be automated.
2. Can we do all of this from an install script?
3. Log directory and file need to be created; app should probably try/except a mkdir and touch on start.

