from flask import Flask, jsonify, request, abort
from typing import Optional
#from json import dumps

from dct_backend.retrieve_coefficients import prepare_coefficients, average_coefficients
from database_config import *
import influx_database as idb
import mysql_database as msq
from validity_tests import *

class sqlTableWorker:
    def __init__(
            self, 
            table, # The table to operate on
            http_request: Optional[object] = None # Flask HTTP request; used to modify rows
            ):
        # Get basic table information set up
        self.table = table
        self.__table_cols = self.get_columns()
        # List of column names to exclude in cases without sufficient trust
        # TODO: make sure similar protections exist on the database side; views!
        self.__sensitive_columns = ["first_name", "last_name", "password"]
        # Figure out what we're doing here
        self.__request = http_request

    # Return a list of valid columns in the table, or None if query fails
    # Used to validate records
    def get_columns(self):
        try:
            query = 'SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;'
            cols_in_table = [v for vals in (msq.query(query, (self.table,)).values) for v in vals] # Flatten list
            return cols_in_table
        except Exception as ex:
            print(self.table, "could not be retrieved:", ex)
            return None
        
    # Validate that the columns specified by a new record actually exist
    # Return the record with any invalid columns dropped (TODO: this may be
    # an information leak vector; adjust to True/False?)
    def check_against_columns(self, record: dict):
        # Get the list of valid columns for the table
        keys = record.keys()
        # Detect invalid columns
        invalid_keys = []
        for key in keys:
            if key not in self.__table_cols:
                invalid_keys.append(key)
        # Remove invalid column keys from the dict and give feedback
        # TODO: API feedback on what got dropped
        for badkey in invalid_keys:
            print(f"{badkey} is not in {self.table}; dropping and continuing")
            del record[badkey]
        # Check for missing columns, fill with None for later imputation
        for col in self.__table_cols:
            if col not in record.keys():
                record[col] = None
        # TODO: what if needed rows are missing? e.g. ID row
        # Return the legitimate record
        return record
    
    # Determine if the types of the record match the types of the database
    # Return a dictionary describing which types match and which don't
    # TODO: attempt to coerce types, yes or no?
    def check_types(self, record):
    # Assumption: all columns are filled in the record prior to reaching this function
    # Retrieve the types of the table's columns and validate
    # the supplied record fields as being the right type.
        query = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;"
        types = msq.query(query, (self.table,))
        match = {}
        for i in len(types): # For every entry in the record
            item_type = type(record[i]) # Get the type of that part of the record
            # Get the corresponding column's type and convert to the Python 
            # equivalent for comparison
            col_type = msq.convert_to_python_type(types[i])
            if item_type != col_type:
                # TODO: SHOULD we coerce the type into the correct one if possible? 
                # (eg int -> float can be done; forcing float only is overly restrictive)
                # On the other hand, type coercion could allow invalid data if abused
                match[types[i]] = False
                print(f"Type of column {i}: {record[i]} ({item_type}) does not match database; must be {col_type}.)")
            else:
                match[types[i]] = True # Types match, good to go
        return match
    
    # Hash a value using password standards
    # Used to protect data before it's stored in the database (passwords)
    def hash_value(self, value):
        # https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html#pbkdf2
        # NIST FIPS-140; pbkdf2 is used here; check iteration count for final. Temp value for testing is small.
        value = crypt(value, iterations=6000)
        return value
    
    # Prepare a record to be inserted into a table
    # TODO: there has to be a more compact way to handle special cases, right?
    def build_record(
        self,
        id_col_name: str, # The name of the ID column for this table; used to build self links
        resource_name: str, # The corresponding resource name for this table; used to build uplinks
        request # The HTTP request; needed to get params
    ):
        row = {}
        # Build record from supplied column names, getting from request as needed
        for col in self.__table_cols:
            # The primary key column
            if col == id_col_name:
                record_id = self.__request.values.get(col) # Used to build self link
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
            elif col == "up_link_href" and resource_name != None:
                upname = "/speedes/1_0/" + resource_name
                if upname[-1] != "/": # Uniform formatting, please
                    upname += "/"
                row[col] = "/speedes/1_0/" + resource_name + "/"
            elif col == "up_link_rel" and resource_name != None:
                row[col] = "up"
            elif col == "self_link_href" and resource_name != None:
                try:
                    row[col] = "/speedes/1_0/" + resource_name + str(record_id)
                except:
                    # For now, this works, but there's a better way somewhere
                    return "Columns out of order" # TODO: is this always the case?
            elif col == "self_link_rel" and resource_name != None:
                row[col] = "self"
            # Date columns that need to be generated
            elif col == "published" or col == "updated":
                row[col] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            elif "password" in col:
                # Store as a hash, not the raw password!
                row[col] = hash_value(self.__request.values.get(col))
            # Other columns that need to be requested from http
            else:
                row[col] = self.__request.values.get(col)
        # Flatten the dictionary into just the values and return for use
        # as a new record
        record = tuple(row.values())
        return record

    # Add a new record to the table
    # Also calls checks to validate said record
    def add_record(self, record: dict):
        pass

    def update_record(self, record_id: int, new_data: dict):
        pass