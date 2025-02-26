#!/bin/bash

# Setup venv

# Ensure necessary commands and libraries are installed
bash ./setup/install_requirements.sh

# Build databases
bash ./setup/install_influx.sh
python ./setup/setup_databases_from_sampledata.py

# Direct user towards documentation