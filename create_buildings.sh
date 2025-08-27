#!/bin/bash

# Will be used later to export created buildings to JSON for use in testing
export_to_json() {
    echo -n "Export virtual buildings to JSON for use in Influx database? y/n: "
    read export
    if [ $export == "y" ]; then
        echo "Check top of file for settings."
        python export_buildings.py
    else
        echo "Export can be performed later by running setup/exports_imports/export_buildings.py"
    fi
    return 0
}

# Prep to create buildings by entering correct directory
cd setup/exports_imports/building_aggregation
# Figure out what kind of buildings to create
echo -e "Buildings may be created in various sizes. These sizes can be randomly sampled from\na distribution of real-world building sizes according to settings in \nsetup/exports_imports/building_aggregation/config.py."
echo "Alternatively, 20 buildings may be created at different sizes, with building 1 having 2 meters,\nbuilding 2 having 3 meters... etc. up to a size of 20."
echo -n "To select random sizes from distribution, enter 1. To select 20 buildings, enter 2. To cancel, enter anything else: "
read opcode

# Make buildings using settings in config.py
if [ $opcode -eq 1 ]; then
    # First confirm that the settings are acceptable
    cat config.py
    confirm=""
    echo -n "Are these settings okay? y/n: "
    read confirm
    while [ $confirm != "y"]; do
        nano config.py
        echo -n "Are these settings okay? y/n: "
        read confirm
    done
    # If all is well, make the buildings
    echo "Creating buildings (please wait)..."
    python create_buildings.py random
    echo "Done."
    # setup/exports_imports/
    cd ..
    export_to_json
# Make 20 buildings, one of each size 2-20
elif [ $opcode -eq 2 ]; then
    echo "Creating buildings (please wait)..."
    python create_buildings.py sizerange
    echo "Done."
    # setup/exports_imports/
    cd ..
    export_to_json
else
    echo "Quitting."
fi