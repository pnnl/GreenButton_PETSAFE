#!/bin/bash

# MySQL
bash api/setup_databases.sh

# Influx
python setup/setup_influx_from_sampledata.py