#!/bin/bash

cd ~/omf
git pull
cd ~/r3it
git pull
sudo systemctl stop r3it
sudo systemctl start r3it
