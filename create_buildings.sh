#!/bin/bash
cd setup/exports_imports/building_aggregation

cat config.py
echo "Preparing to aggregate raw metering data into virtual buildings."

confirm=""
echo -n "Are these settings okay? y/n: "
read confirm

while [ $confirm != "y"]; do
    nano config.py
    echo -n "Are these settings okay? y/n: "
    read confirm
done


echo "Creating buildings (please wait)..."
python create_buildings.py
echo "Done."

# setup/exports_imports/
cd ..
echo -n "Export virtual buildings to JSON for use in Influx database? y/n: "
read export

if [ $export == "y" ]; then
    echo "Check top of file for settings."
    python export_buildings.py
else
    echo "Export can be performed later by running setup/exports_imports/export_buildings.py"
fi