import pymysql
import json
import pandas as pd
from database_config import *
from typing import Optional
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
def query(
        query: str,
        params: Optional[tuple] = None
        ):
    conn = connect_DB()
    #results = pd.read_sql(query, conn)
    with conn.cursor() as cursor:
        # escape_string() doesn't handle backticks
        query = conn.escape_string(query).replace('`', '``')
        if params == None:
            result_rows = cursor.execute(query)
        else:
            result_rows = cursor.execute(query, params)
        results = cursor.fetchall()
    close_conn(conn)
    try:
        results = pd.DataFrame.from_records(results)
        if results.empty:
            return 404
    except Exception as ex:
        print(ex)
        print(results)
    return results

def update_record(record_id, column, new_value, table):
    if type(record_id) is not int: # Try to limit attempts to modify the whole table
        return "Record id must be a single integer."
    conn = connect_DB()
    # Table name can't be parameterized normally; we have to do it manually
    # escape_string() mostly handles this but ignores backticks
    # That makes backticks a potential problem; we need to escape them to prevent problems
    # Escaping backticks = double backtick, not backslash as usual
    escaped_table = conn.escape_string(table).strip('`').replace('`', '``')
    # Also escape the record_id, column, etc. and get it into a good format for use
    record_id = conn.escape_string(str(record_id))
    column = conn.escape_string(column)
    new_value = conn.escape_string(str(new_value))
    try:
        with conn.cursor() as cursor:
            # Get ID column name for table
            id_col = None # Placeholder
            query = f"""UPDATE {table}
                    SET %s = %s WHERE {id_col} = %s"""
            cursor.execute(query, (column, new_value, record_id))
            status = 200
    except Exception as status:
        print(status)
        status = 500
    close_conn(conn)
    return status

def insert_MySQL(columns: tuple, record: tuple, table: str):
    # Note: For DST, supply rules in the form specified at https://www.greenbuttonalliance.org/daylight-savings-time
    # Verify record is in usable format
    if type(record) not in (list, tuple):
        return "Record must be a list or tuple"
    conn = connect_DB()
    # Table name can't be parameterized normally; we have to do it manually
    # escape_string() mostly handles this but ignores backticks
    # That makes backticks a potential problem; we need to escape them to prevent problems
    # Escaping backticks = double backtick, not backslash as usual
    escaped_table = conn.escape_string(table).strip('`').replace('`', '``')
    # Insert the query if all is well
    with conn.cursor() as cursor:
        try:
            # Time to try the actual insert query
            query = f"INSERT INTO {escaped_table} %s VALUES %s"
            cursor.execute(query, (columns, record))
            conn.commit()
            status = 201
            query = f"SELECT * FROM {table} WHERE id = %s;"
            values = pd.DataFrame.from_records(record)
        except Exception as ex:
            print(ex)
            status = 500
            return status, None
    close_conn(conn)
    return status, values

def delete_record(id, table):
    conn = connect_DB()
    # Table name can't be parameterized normally; we have to do it manually
    # escape_string() mostly handles this but ignores backticks
    # That makes backticks a potential problem; we need to escape them to prevent problems
    # Escaping backticks = double backtick, not backslash as usual
    escaped_table = conn.escape_string(table).strip('`').replace('`', '``')
    with conn.cursor() as cursor:
        try:
            # TODO: get id row name for id selection
            query = f"DELETE FROM {table} WHERE id = %s"
            cursor.execute(query, (id,))
            conn.commit()
            status = 200
        except Exception as ex:
            print(ex)
            status = 500
    close_conn(conn)
    return status

# Takes a MySQL column datatype and outputs the corresponding
# Python type, using the built-in pymysql mapping
# (see here: https://github.com/PyMySQL/PyMySQL/blob/main/pymysql/converters.py )
def convert_to_python_type(msq_datatype: str):
    type_mapping = pymysql.converters.decoders
    try:
        python_type = type_mapping[msq_datatype]
        return python_type
    except Exception as ex:
        print("Cannot convert type:", ex)
        return None

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