#!/bin/bash
read -p "Enter username: " user
read -p "Enter new PAT: " pat
git remote set-url origin https://$user:$pat@gitlab.pnnl.gov/DigitalPrivacy/PETSAFE.git/