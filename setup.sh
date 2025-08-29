#!/bin/bash

# Prepare the API's backend requirements

echo -e "Setup script assumes an Ubuntu environment; if installation of databases \nfails, check package names."

# Ensure we can see Python files here- corrects a bug where relative imports don't work
PYTHONPATH="$PYTHONPATH:/home/petsafe/Desktop/PETSAFE"

# Ensure necessary commands and libraries are installed
bash setup/install_requirements.sh

#Create databases
bash setup/install_influx.sh
bash setup/install-mysql.sh

# Fill  databases
# MySQL
bash ./populate_mysql.sh
# Influx
python ./setup_influx_from_sampledata.py

# TODO: Direct user towards documentation