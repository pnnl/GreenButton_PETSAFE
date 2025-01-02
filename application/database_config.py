from os import environ
METER_DATABASE_PATH = "data/records.db"

# TODO: TEMP! Change once Influx is implemented
# (and lock down path traversal)
BUILDING_DATABASE_PATH = "../data/buildings/"

host = "http://127.0.0.1:8086"
bucket = "Buildings"
token = environ.get("INFLUXDB_TOKEN")
org = "PNNL"