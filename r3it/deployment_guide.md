Deploy:
1. Create an Ubuntu 20.04 VM with at least 1 vCPU and 2GB ram.
2. Configure DNS to point to new VM.
3. Ensure ports 443 and 80 are open (e.g., on hosting provider's firewall).
4. Clone the repo: git clone https://github.com/dpinney/r3it
5. Edit config.py, adding API keys, domain name, emails, etc. as appropriate.
6. Run install.sh as root, e.g., sudo bash ~/r3it/install.sh

Update:
1. sudo bash ~/r3it/r3it/pull_update.sh

Issues: 
1. Can we do all of this from an install script? Yes! We can do `pip install git+https://github.com/dpinney/r3it` and it should all just run. Here's [an example](https://raw.githubusercontent.com/dpinney/senesce/master/setup.py?token=AAQIL3VLOWXQMJ2HWLK4K7TADQXP4) of triggering arbitrary commands in a pre/post install.
3. Log directory and file need to be created; app should probably try/except a mkdir and touch on start.
