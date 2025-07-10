#!/bin/bash

# Ensure we can see Python files here
PYTHONPATH="$PYTHONPATH:/home/petsafe/Desktop/PETSAFE"

# Setup venv
cd setup

# Ensure necessary commands and libraries are installed
bash install_requirements.sh

#Create databases
bash install_influx.sh
bash install-mysql.sh

# Fill  databases
# MySQL
bash ./populate_mysql.sh
# Influx
python ./setup_influx_from_sampledata.py

# Direct user towards documentation