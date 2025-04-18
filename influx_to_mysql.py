from api import influx_database as idb
from database_config import *
import pandas as pd

def build_sql():
    # query holds the final contents of our output file; i.e. a SQL file that
    # will populate the MySQL database with metering data
    query = "START TRANSACTION;\n"
    print(f"Start date: {data_startdate}")
    print(f"End date: {data_enddate}")
    # Retrieve data from Influx database
    idb_query = f'from(bucket:"Buildings") \
|> range(start: {data_startdate}, stop: {data_enddate}) \
|> filter(fn:(r) => r._measurement == "power" and r._field == "real_power")'
    metering_data = idb.query(idb_query)

    # Format metering data
    # Remove unnecessary columns
    for column in metering_data:
        if column in ["result", "table", "_measurement", "privacy", "meter_type", "_start", "_stop"]:
            del metering_data[column]
    # Fix column naming schemes for ease of use
    metering_data.rename(columns={"_time": "timestamp", "_value": "value", "_field": "measurement"}, inplace=True)

    print("Data retrieved. Formatting into MySQL inserts...")

    # Change timestamps to UNIX time for format compatibility
    metering_data["timestamp"] = pd.to_datetime(metering_data["timestamp"]).map(pd.Timestamp.timestamp).apply(int)
    # Power units are kW by default with 3 points of decimal precision (0.000), but the value column is bigint.
    # Convert to Watts (* 1000) ; ensure that corresponding ReadingType has correct power of ten multiplier (0 for Watts)
    metering_data["value"] = (metering_data["value"] * 1000).apply(int)
    query = query + "/* Note: Value unit is Watts */\n"

    # For each record: build the line inserting it into MySQL's database
    print(f"Creating SQL inserts from {len(metering_data)} rows.")
    row_id = 0
    try:
        for row in metering_data.index:
            row_data = metering_data.iloc[row]
            # Duration is in seconds: 900 seconds = 15 minutes
            # CPP = 0 means "not applicable"
            query = query + 'INSERT INTO interval_readings (id, cost, duration, start, value, interval_block_id, consumptionTier, tou, cpp) ' + \
                f'VALUES ({row_id}, "", 900, {row_data["timestamp"]}, {row_data["value"]}, "", "", "", 0);\n'
            row_id += 1
    except KeyboardInterrupt:
        print("Stopping.")
    query = query + "\nCOMMIT;"
    return query

def main():
    print("Retrieving data.")
    sql_query = build_sql()
    outfile_name = "populate_mysql_meter_data.sql"
    with open(outfile_name, "w") as outfile:
        outfile.write(sql_query)
    print(f"Done. Data output to {outfile_name}")

main()