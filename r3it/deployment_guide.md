Deploy:
1. Create an Ubuntu 20.04 VM
2. Configure DNS to point to new VM.
3. Edit config.py, put in API keys, domain name, etc. as appropriate.
4. Run install.sh

Update:
1. sudo bash ~/r3it/r3it/pull_update.sh

Issues: 
1. Can we do all of this from an install script? Yes! We can do `pip install git+https://github.com/dpinney/r3it` and it should all just run. Here's [an example](https://raw.githubusercontent.com/dpinney/senesce/master/setup.py?token=AAQIL3VLOWXQMJ2HWLK4K7TADQXP4) of triggering arbitrary commands in a pre/post install.
3. Log directory and file need to be created; app should probably try/except a mkdir and touch on start.
