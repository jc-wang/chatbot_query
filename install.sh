#!/bin/bash
# Installing
sudo pip3 install -r requirements.txt
sudo python3 setup.py install
# Deleting trash files
sudo rm -r build/ || true
sudo rm -r dist/ || true
sudo rm -r chatbotQuery.egg-info/ || true
#if  [ -d "$build"]; then
#    sudo rm -r build/
#fi
#if  [ -d "$dist"]; then
#    sudo rm -r dist/
#    sudo rm -r chatbotQuery.egg-info/
#fi
