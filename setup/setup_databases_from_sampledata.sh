#!/bin/bash

# Influx
python setup_influx_from_sampledata.py

# MySQL
bash ./api/setup_databases.sh