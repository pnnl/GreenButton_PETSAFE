import pymysql
import json
import pandas as pd
#from pandas.io.json import json_normalize
from os import environ
# TODO: document setup

token = environ.get("SQL_PASS")

# Open a connection to the database.
def connect_DB():
    # TODO: Consider putting user info in environment variables too
    conn = pymysql.connect(
        host='localhost',
        user='dataowner',
        password=token,
        db='meters',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor # Returns queries as dict
    )
    return conn

def insert_MySQL(record):
    pass
    # conn.commit()

def import_from_json(filepath):
    # Read the JSON file
    json_data=open(filepath).read()
    json_obj = json.loads(json_data)
    # Sanitize the data
    # json_data = pymysql.escape_string(json_data)
    # Write to database
    conn = connect_DB()
    cursor = conn.cursor()
    #data = json_normalize(json_obj)
    print(data)
    #cursor.execute("INSERT INTO testp (person,	year,	company) VALUES (%s,	%s,	%s)", (person,	year,	company))
    # Commit changes
    # conn.commit()
    conn.close()

# Retrieve data about individual meters
def import_meter_metadata():
    # Ensure tables exist
    # Read meter points into a frame
    read_from_file = "../data/points.csv"
    point_data = pd.read_csv(read_from_file, sep=",", header=0).convert_dtypes(convert_string=False)
    #print(point_data)
    # Format the frame for GB compatibility
    # Place the frame in a table
    # Read the meter sites into a frame
    read_from_file = "../data/sites.csv"
    site_data = pd.read_csv(read_from_file, sep=",", header=0).convert_dtypes(convert_string=False)
    print(site_data)
    # Format the frame for GBA compatibility
    # Place the frame in a table


def read_building_metadata(building_id, conn):
    pass

def close_conn(conn):
    try:
        conn.close()
    except:
        print("Cannot close connection. Does connection exist?")


def main():
    # Read metadata for individual meters
    import_meter_metadata()
    raise SystemExit
    # Read metadata for composite building meters
    from dct_backend import list_files
    read_from_dir = "./import-to-database/raw/"
    for file in list_files.list_files_in_dir(read_from_dir, append_path=True):
        print("Reading", file)
        # TODO: incorporate metadata (in its own bucket?)
        if "metadata" in file:
            import_from_json(filename=file)
        else: # not a metadata file
            pass

if __name__ == "__main__":
    main()