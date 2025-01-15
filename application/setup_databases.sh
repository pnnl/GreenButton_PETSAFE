#!/bin/bash

# Root not needed
if [ $(whoami) = "root" ]; then
    echo "Root user not required for setup; please run as regular user if possible."
fi

# Run from within the application directory or be corrected
dir=$(basename pwd)
if [ dir != "application" ]; then
    echo "Please run script from within application directory."
    cd application
fi

# --------- Influx -------------
echo "Setting up Influx database..."
# Clean out database if it exists already, then import aggregate buildings
python influx_database.py
# Import raw meters (this will take a while)
python import_meters.py

# --------- MySQL -------------
echo "Setting up MySQL databases..."
# Clear out database if it already exists, then set up and prepopulate
bash ./sql/init_databases.sh