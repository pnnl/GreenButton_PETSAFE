from os import environ
# Used pretty much exclusively by influx_to_mysql.py

METER_DATABASE_PATH = "/mnt/hgfs/records.db"

# TODO: TEMP! Change once Influx is fully implemented
BUILDING_DATABASE_PATH = "../data/buildings/"

# Influx information
influx_host = "http://127.0.0.1:8086"
influx_bucket = "Buildings"
influx_token = environ.get("INFLUXDB_TOKEN")
influx_org = "PNNL"

# MySQL information
mysql_host = "localhost"
mysql_user = "root" #"dataowner"
mysql_token = environ.get("SQL_PASS")
mysql_db = 'datacustodian'

# UUID info
domain = "speedes.pnnl.gov"
url = "https://" + domain

# Date range to work with
data_startdate = "2023-01-01T00:00:00Z"
data_enddate = "2024-01-01T00:00:00Z"