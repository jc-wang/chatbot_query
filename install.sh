#!/bin/bash
# Installing
sudo pip3 install -r requirements.txt
sudo python3 setup.py install
# Deleting trash files
sudo rm -r build/
sudo rm -r dist/
sudo rm -r chatbotQuery.egg-info/
