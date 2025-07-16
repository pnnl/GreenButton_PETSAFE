import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime as dt
from processor.commonDB import DBConn
import plotly.express as px

UTC = ZoneInfo("UTC")
local = ZoneInfo('America/Los_Angeles')

METER_DATABASE_PATH = "/mnt/hgfs/records.db"

def get_mains_meter():
    meter_id = 33342
    start_date = dt.strptime("2023-05-01", "%Y-%m-%d").timestamp()
    end_date = dt.strptime("2023-05-02", "%Y-%m-%d").timestamp()
    query = f"SELECT * FROM POWER WHERE point_id == {meter_id} AND timestamp BETWEEN '{start_date}' AND '{end_date}'"
    # Site 33392 has solar
    # Retrieve a day or two, plot it, and see what happens
    # Retrieve the meter's data
    with DBConn.create_connection(METER_DATABASE_PATH) as conn:
        print("Retrieving...")
        try:
            results = conn.execute(query)
            data = []
            cursor_obj = conn.cursor()
            # Retrieve the rows queried. This is the relative slow step in querying; it runs quickly
            # for 2 units but slows down as more units are added to the building and more rows must be
            # retrieved.
            # TODO: Test values for best speed. 10000 better than 100000; will smaller help even more?
            cursor_obj.arraysize = 10000 # May speed up retrieval; sets how many rows are fetched by fetchmany()
            while True:
                # Fetchmany allows both performance improvements over fetchall() and prevents MemoryError for invalid id values
                chunk = results.fetchmany()
                if chunk == []: # fetchmany returns empty list if there are no more results
                    break
                else:
                    data = data + chunk # Append to list of records
            print("Retrieved. Cleaning up (do not interrupt)...")
            try:
                cursor_obj.execute("PRAGMA optimize;")
                cursor_obj.close()
            except KeyboardInterrupt:
                cursor_obj.close()
        except Exception as ex:
            print(ex)
        # Needed to concatenate frames properly because from_records() needs a list of columns
        columns = ['ee_site_id', 'point_id', 'timestamp', 'duration', 'real_power', 'apparent_power', 'pf'] # used for frame creation
        # Transfer records into a data frame for easier processing
        if 'bdata' not in locals(): # Frame does not exist yet
            bdata = pd.DataFrame.from_records(data=data, columns=columns)
        else: # Frame exists; add new data to existing frame
            newframe = pd.DataFrame.from_records(data=data, columns=columns)
            bdata = pd.concat([bdata, newframe])
    power = pd.DataFrame()
    power["timestamp"] = bdata["timestamp"]
    power["real_power"] =bdata["real_power"]
    power['timestamp'] = pd.to_datetime(power['timestamp'],unit='s')
    power = power.set_index("timestamp")
    print(power)

    # Plot power over the course of the day
    title = "Power Output of Solar Meter 33342"
    fig = px.line(power, y="real_power", title=title)
    fig.show()

def get_solar_from_csv():
    year = "2023"
    month = "03"
    day = "20" # Solar equinox
    filepath = f"/mnt/hgfs/{year}-Full_v8.1/{year}/power/power-fifteen-{year}{month}{day}.csv"
    data = pd.read_csv(filepath)
    # We need a site with a solar-only meter
    site = 521
    circuit = "CIRCUIT_27"
    # Another one!
    site = 727
    circuit = "CIRCUIT_13"
    solar = data.loc[(data["regname"] == circuit) & (data["ee_site_id"] == site)].copy()
    solar["min_t"] = pd.to_datetime(solar['min_t'], format="ISO8601")
    solar = solar.set_index("min_t")
    print(solar)
    # Plot power over the course of the day
    title = f"Power Output of Site {site}, Circuit {circuit} (Solar PV) on {year}-{month}-{day}"
    fig = px.line(solar, y="power", title=title)
    fig.show()

def main():
    #get_mains_meter()
    get_solar_from_csv()

main()