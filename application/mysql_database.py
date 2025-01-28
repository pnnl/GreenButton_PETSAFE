import pymysql
import json
import pandas as pd
from database_config import *
# TODO: document setup

# Open a connection to the database.
def connect_DB():
    # TODO: Consider putting user info in environment variables too
    conn = pymysql.connect(
        host=mysql_host,
        user=mysql_user,
        password=mysql_token,
        db=mysql_db,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor # Returns queries as dict
    )
    return conn

# Query the database
# We're not allowing fully user-written queries, but it doesn't hurt
# to check the application query for safety anyway; maybe someone
# managed to find a way to add more inputs or otherwise cause
# problems. Let's not make injection easy on them.
def query(query):
    conn = connect_DB()
    #results = pd.read_sql(query, conn)
    with conn.cursor() as cursor:
        # escape_string() doesn't handle backticks
        query = conn.escape_string(query).replace('`', '``')
        result_rows = cursor.execute(query)
        results = cursor.fetchall()
        #fetched = results.fetchall()
    close_conn(conn)
    results = pd.DataFrame.from_records(results)
    return results

def update_record(record_id, column, new_value, table):
    if type(record_id) is not int: # Try to limit attempts to modify the whole table
        return "Record id must be a single integer."
    # Table name can't be parameterized normally; we have to do it manually
    # escape_string() mostly handles this but ignores backticks
    # That makes backticks a potential problem; we need to escape them to prevent problems
    # Escaping backticks = double backtick, not backslash as usual
    escaped_table = pymysql.escape_string(table).strip('`').replace('`', '``')
    # Also escape the record_id, column, etc. and get it into a good format for use
    record_id = pymysql.escape_string(str(record_id))
    column = pymysql.escape_string(column)
    new_value = pymysql.escape_string(str(new_value))
    conn = connect_DB()
    try:
        with conn.cursor(prepared=True) as cursor:
            # Get ID column name for table
            id_col = None # Placeholder
            query = f"""UPDATE {table}
                    SET %s = %s WHERE {id_col} = %s"""
            cursor.execute(query, (column, new_value, record_id))
            status = "Success"
    except Exception as status:
        print(status)
    close_conn(conn)
    return status

def insert_MySQL(record, table):
    # Note: For DST, supply rules in the form specified at https://www.greenbuttonalliance.org/daylight-savings-time
    # Verify record is in usable format
    if type(record) not in (list, tuple):
        return "Record must be a list or tuple"
    # Table name can't be parameterized normally; we have to do it manually
    # escape_string() mostly handles this but ignores backticks
    # That makes backticks a potential problem; we need to escape them to prevent problems
    # Escaping backticks = double backtick, not backslash as usual
    escaped_table = pymysql.escape_string(table).strip('`').replace('`', '``')
    # Escape new record contents to protect against some injection attacks
    # Parameterization also escapes it for pymysql, but doesn't hurt to be sure it happened
    record = pymysql.escape_string(record)
    # Insert the query if all is well
    conn = connect_DB()
    with conn.cursor(prepared=True) as cursor:
        try:
            # Time to try the actual insert query
            query = f"INSERT INTO '{escaped_table}' VALUES (%s)"
            cursor.execute(query, (record,))
            query = f"SELECT * FROM '{escaped_table}'"
            results = cursor.execute(query)
            print(results.fetchall())
            #conn.commit()
            conn.rollback() # For testing
            status = "Success"
        except Exception as ex:
            print(ex)
            status = ex
    close_conn(conn)
    return status

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
    #print(data)
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