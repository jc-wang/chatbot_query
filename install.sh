#!/bin/bash
# Installing
sudo pip3 install -r requirements.txt
sudo python3 setup.py install
sudo python3 -m textblob.download_corpora
# Deleting trash files
sudo rm -r build/ || true
sudo rm -r dist/ || true
sudo rm -r chatbotQuery.egg-info/ || true
