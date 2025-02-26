#!/bin/bash

# Ubuntu and Debian
# Add the InfluxData key to verify downloads and add the repository
echo "Downloading Influx repository key."
curl --silent --location -O \
https://repos.influxdata.com/influxdata-archive.key
echo "Validating key and adding Influx to repository list."
echo "943666881a1b8d9b849b74caebf02d3465d6beb716510d86a39f6c8e8dac7515  influxdata-archive.key" \
| sha256sum --check - && cat influxdata-archive.key \
| gpg --dearmor \
| tee /etc/apt/trusted.gpg.d/influxdata-archive.gpg > /dev/null \
&& echo 'deb [signed-by=/etc/apt/trusted.gpg.d/influxdata-archive.gpg] https://repos.influxdata.com/debian stable main' \
| tee /etc/apt/sources.list.d/influxdata.list
# Install influxdb
echo "Installing Influx with apt-get."
sudo apt-get update && sudo apt-get install influxdb2
# Starting Influx.
echo "Starting Influx."
sudo service influxdb start
# Show that it's active
sudo service influxdb status | head -n 5 | tail -n 1
echo "InfluxDB available at localhost:8086 by default. Change this if necessary;"
echo "see https://docs.influxdata.com/influxdb/v2/reference/config-options/"
return 0