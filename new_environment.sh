#!/bin/bash -vx
apt-get install awscli
aws configure
sudo apt-get install python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
sudo snap install terraform

