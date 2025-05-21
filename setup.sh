#!/bin/bash

# Setup venv
cd setup

# Ensure necessary commands and libraries are installed
bash install_requirements.sh

#Create databases
bash install_influx.sh
bash install-mysql.sh

# Fill  databases
cd ..
python setup_databases_from_sampledata.py

# Direct user towards documentation