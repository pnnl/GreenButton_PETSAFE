from flask import abort
from datetime import datetime
from database_config import *
import influx_database as idb
import mysql_database as msq
from datetime import datetime as dt
from uuid import uuid4
from pbkdf2 import crypt
from typing import Optional
#from json import dumps

def get_cols_in_table(table):
    query = 'SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;'
    cols_in_table = [v for vals in (msq.query(query, (table,)).values) for v in vals] # Flatten list
    return cols_in_table


# Verify that a list of keys corresponds with columns in a table
# keys: the list of column names to test
# table: the name of the table to test on
def check_against_columns(
        key_dict: dict, 
        table: str,
        return_invalid_keys: Optional[bool] = False
        ):
    # TODO: Also check types of data for validity?
    # Get the list of valid columns for the table
    keys = key_dict.keys()
    cols_in_table = get_cols_in_table(table)
    # Detect invalid columns
    invalid_keys = []
    for key in keys:
        if key not in cols_in_table:
            invalid_keys.append(key)
    # Remove invalid column keys from the dict and give feedback
    # TODO: API feedback on what got dropped
    for badkey in invalid_keys:
        print(f"{badkey} is not in {table}; dropping and continuing")
        del key_dict[badkey]
    # Check for missing columns, fill with None for later imputation
    for col in cols_in_table:
        if col not in key_dict.keys():
            key_dict[col] = None
    # TODO: what if needed rows are missing? e.g. ID row
    # Return the legitimate keys; optionally, also return the invalid keys
    if return_invalid_keys == True:
        return key_dict, invalid_keys
    else:
        return key_dict

# Checks for start and end date arguments in routing, then ensures
# that the dates are valid, exist in the data, and that end > start.
# Returns the dates if these checks pass.
# request: the HTTP request
def check_for_date_limiter_arguments(request):
    # Fallbacks
    # TODO: fall back to whole data span? Or is None sensible? Think about it
    start_date = None
    end_date = None
    # Determine if we have any date filtering
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    try: # Validity check: are these dates formatted in a valid way?
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d")
        if dt_start and dt_end:
            assert dt_end > dt_start # Does end come AFTER start? If not, request is malformed
    except (ValueError, AssertionError): # Malformed date
        abort(400)
    # TODO sanity check: do we HAVE these dates available? If not, 404
    return start_date, end_date

# Check that the requested ID actually exists
# If it does, returns the id
# Otherwise, aborts request (404: building does not exist, not found error)
# id: the id to check
def sanity_check_building_id(meter_id):
    try:
        # TODO: parameterize, not fstring
        #"SELECT real_power FROM POWER WHERE building_id = {id} LIMIT 1;""
        query = f'from(bucket:"{influx_bucket}")\
        |> range(start: {data_startdate}, stop: {data_enddate})\
        |> filter(fn:(r) => r._measurement == "power" and r._field == "real_power" and r.meter_id == "{meter_id}")\
        |> limit(n: 1)'
        results = idb.query(query=query)
    except Exception as ex:
        print("Could not verify that meter ID", meter_id, "exists:", ex)
        # Refine this as needed; for now, assume the code is at fault
        abort(500)
    # Test if we have any results
    if not results.empty:
        return meter_id # Building exists
    else:
        print("Building not found in Influx database.")
        abort(404) # Building does not exist; bad request

def hash_value(value):
    # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2
    # NIST FIPS-140; pbkdf2 is used here; check iteration count for final. Temp value for testing is small.
    value = crypt(value, iterations=6000)
    return value

# Determine if the types of the record match the types of the database
def check_types(record, table):
    # Assumption: all columns are filled in the record prior to reaching this function
    # Retrieve the types of the table's columns and validate
    # the supplied record fields as being the right type.
    query = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;"
    types = msq.query(query, (table,))
    match = []
    for i in len(types): # For every entry in the record
        item_type = type(record[i]) # Get the type of that part of the record
        # Get the corresponding column's type and convert to the Python 
        # equivalent for comparison
        col_type = msq.convert_to_python_type(types[i])
        if item_type != col_type:
            # TODO: SHOULD we coerce the type into the correct one if possible? 
            # (eg int -> float can be done; forcing float only is overly restrictive)
            # On the other hand, type coercion could allow invalid data if abused
            match.append(False)
            print(f"Type of column {i}: {record[i]} ({item_type}) does not match database; must be {col_type}.)")
        else:
            match.append(True) # Types match, good to go
    return match

# Get variable number of arguments and format into a record
# Some fields need to be auto-generated; others will need to be
# provided by the user. This function handles both and returns
# a record composed of the specified columns.
# column_names: the names of the columns in the table
# id_col_name: the primary key column name for the table (TODO: what if multi-level key?)
# uplink: the unique part of the uplink. Excludes naming/versioning.
# e.g. "customers/" is correct; "/speedes/1.0/customers/" is not.
# request: the HTTP request. Needed to get values for user-supplied params.
def build_record(
        column_names: list, # Ensure these are in order!
        id_col_name: str,
        uplink: str,
        request # The HTTP request; needed to get params
):
    row = {}
    # Build record from supplied column names, getting from request as needed
    for col in column_names:
        # The primary key column
        if col == id_col_name:
            record_id = request.values.get(col) # Used to build self link
            row[col] = record_id
        # UUID column
        elif col == "uuid":
            row[col] = uuid4() #uuid5(mysql_host, id)
        # bool columns
        elif col in ["enabled"]:
            try:
                row[col] = bool(request.values.get(col))
            except:
                print(col, "must be convertable to a Boolean value")
        # Uplinks and self links
        elif col == "up_link_href" and uplink != None:
            row[col] = "/speedes/1_0/" + uplink
        elif col == "up_link_rel" and uplink != None:
            row[col] = "up"
        elif col == "self_link_href" and uplink != None:
            try:
                row[col] = "/speedes/1_0/" + uplink + str(record_id)
            except:
                # For now, this works, but there's a better way somewhere
                return "Columns out of order" # TODO: is this always the case?
        elif col == "self_link_rel" and uplink != None:
            row[col] = "self"
        # Date columns that need to be generated
        elif col == "published" or col == "updated":
            row[col] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        elif "password" in col:
            # Store as a hash, not the raw password!
            row[col] = hash_value(request.values.get(col))
        # Other columns that need to be requested from http
        else:
            row[col] = request.values.get(col)
    # Flatten the dictionary into just the values and return for use
    # as a new record
    record = tuple(row.values())
    return record

def update_row(
        table: str, 
        new_data: dict # Must include the ID column of the row to change
        ):
    # Validate that the columns we're asking to change actually exist
    new_data = check_against_columns(new_data, table)
    # For columns with a value of None, grab the old value from the table
    none_cols = [col for col in new_data.keys() if new_data[col] == None]
    #none_cols = ", ".join(none_cols) # Format for query
    # TODO: some tables have different id column names. Account for that.
    row_id = new_data["id"]
    query = f"SELECT * FROM {table} WHERE id = %s;"
    values = msq.query(query, (row_id,))
    # Overwrite the columns listed in new_data with the new data
    for col in new_data:
        if col not in none_cols: # If this column has been supplied with new values to update to
            if "password" in col: # Hash the password column values!
                new_data[col] = hash_value(new_data[col])
            values[col] = new_data[col]
    # Place the values into the table, overwriting the existing row
    query = f"UPDATE {table} SET "
    parameters = []
    for col in new_data:
        query += f"{col} = %s, "
        parameters.append(values[col].iloc[0])
    query = query[:-2] + " " # Remove final comma
    query += f"WHERE id = {row_id};"
    print(query)
    print(parameters)
    try:
        status = msq.query(query, parameters)
        query = f"SELECT * FROM {table} WHERE id = %s;"
        values = msq.query(query, (row_id,))
        return values, 200
    except Exception as ex:
        print("Query failed:", ex)