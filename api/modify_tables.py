from typing import Optional
from uuid import uuid5, NAMESPACE_URL
import argon2 as a2
from datetime import datetime as dt
import pandas as pd
from flask import Response

from database_config import *
import mysql_database as msq

def combine_dict(d1, d2):
    return {
        k: tuple(d[k] for d in (d1, d2) if k in d)
        for k in set(d1.keys()) | set(d2.keys())
    }

# TODO: Check the size of data before passing it to MySQL.

# Perform operations on a MySQL table's data; read, write, delete, etc.
class sqlTableWorker:
    def __init__(
            self, 
            table: str, # The table to operate on
            id_column_name: str, # The name of the ID column used to identify the resource
            http_request: Optional[object] = None, # Flask HTTP request; used to modify rows
            resource_id: Optional[int] = None # The ID of a resource to modify or view
            ):
        # Get basic table information set up
        self.table = self.escape_string(table)
        if self.table is not None:
            self.__table_cols = self.__get_columns()
            self.id_col = id_column_name
            # List of column names to exclude in cases without sufficient trust
            # TODO: make sure similar protections exist on the database side if possible
            self.__sensitive_columns = ["first_name", "last_name", "password"]
            # Figure out what we're doing here
            self.__request = http_request
            self.__resource_id = resource_id
            if self.__resource_id == None:
                try:
                    self.__resource_id = self.__request.values.get("id")
                except:
                    print("No resource ID provided.")
        else:
            print("Cannot initialize tableWorker; table name must be a string of a valid table name.")

    # Escape a string for insertion into the table
    # Requires opening a connection to use escape_string()
    # <- string: the string to escape
    # -> escaped_str or None: the string, post-escaping
    def escape_string(
            self, 
            string: str
            ):
        if isinstance(string, str):
            conn = msq.connect_DB()
            # Backticks are not covered by escape_string
            escaped_str = conn.escape_string(string).strip('`').replace('`', '``')
            msq.close_conn(conn)
            return escaped_str
        else:
            print("Table name must be a string.")
            return None
        
    # Take an HTTP request and perform the relevant operation
    # <- nothing required
    # OPTIONAL <- : an HTTP request from Flask to act on
    # It is preferred that you provide this when opening the Worker, but
    # it is allowed to do so here
    # -> JSON data corresponding to the operation;
    # e.g. a GET request would return JSON data of the table's contents,
    # a POST request would return the updated or added record,
    # a DELETE request would return with whether deletion succeeded
    def perform_request_operation(
            self, 
            flask_response: bool = False,
            request: Optional[object] = None
            ):
        # Test whether we HAVE a request
        if request is None and self.__request is None:
            return "No request"
        # If we're adding a request now, handle that
        elif self.__request is None:
            self.__request = request
        # We have a request; perform the corresponding operation
        # TODO: does the user have permission to do this?
        print("Resource ID:", self.__resource_id)
        try:
            # View the whole table
            if self.__request.method == 'GET' and self.__resource_id is None:
                print("Retrieving records.")
                status, results = self.view_table()
            # View a specific item of the table
            elif self.__request.method == 'GET' and self.__resource_id is not None:
                print("Retrieving record.")
                # TODO: error found when ID is provided - unable to coerce to series, length must be 13; given 0
                status, results =  self.view_record(self.__resource_id)
            # Update a specific item of the table
            elif self.__request.method == 'POST':
                request_contents = dict(self.__request.args)
                # Update an existing record
                if self.__resource_id is not None and self.__check_if_in_table(self.__resource_id) == True:
                    status, results = self.update_record(self.__resource_id, request_contents)
                    print(results)
                # Add a new record
                elif self.__check_if_in_table(self.__resource_id) == False:
                    record = self.__build_record(self.id_col, self.__resource_id, request)
                    status, results = self.add_record(record)
                # Missing information
                else:
                    status = 400
                    results = "Missing resource ID for resource to add or modify"
            # Delete a specific record of the table
            elif self.__request.method == 'DELETE' and self.__resource_id is not None:
                status, results = self.delete_record(self.__resource_id)
            # Catch other cases
            else:
                print("Cannot perform operation; are you missing an argument?")
                status = 400
                results = "Missing required information"
        except Exception as ex:
            print(ex)
            status = 500
            results = "Server error"
        # If we've requested a Flask-style Response, do so. Otherwise, just return the results
        if flask_response == True:
            response = Response(results, status=status, mimetype='application/json')
            return response
        else:
            return status, results
        

    # Return a list of valid columns in the table, or None if query fails
    # Used to validate records
    # <- nothing
    # -> the table's columns as a tuple, or None if columns could not be queried for
    def __get_columns(self):
        try:
            query = 'SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;'
            cols_in_table = tuple([v for vals in (msq.query(query, (self.table,)).values) for v in vals]) # Flatten list
            cols_in_table = tuple(dict.fromkeys(cols_in_table)) # Remove duplicates, keeping order
            return cols_in_table
        except Exception as ex:
            print(self.table, "could not be retrieved:", ex)
            return None
        
    # Validate that the columns specified by a new record actually exist
    # Return the record with any invalid columns dropped 
    # <- record: a dictionary of the record; format {"columnName": value}
    # -> record: the record, with nonexistent columns and corresponding data removed
    # TODO: does the user need more feedback to avoid data loss on insertion typos?
    # (TODO: this may be an information leak vector; adjust to True/False?)
    def __check_against_columns(
            self, 
            record: dict
            ):
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
                record[str(col)] = None
        # TODO: what if needed rows are missing? e.g. ID row
        # Check that id/primary key column is included
        # Return the legitimate record
        return record
    
    # Determine if the types of the record match the types of the database
    # Return a dictionary describing which types match and which don't
    # <- record: the record to check the types of. Must be an iterable.
    # -> match: a dictionary of columns to type correctness; 
    # "key": True means the type is correct for the "key" column,
    # "key": False means the type is incorrect for the "key" column
    # TODO: attempt to coerce types, yes or no?
    def __check_types(
            self, 
            record: tuple # Or list, or set, or other iterable
            ):
        print("WARNING: the function this relies on is not fully implemented (msq.convert_to_python_types()), use at your own risk!")
    # Assumption: all columns are filled in the record prior to reaching this function
    # Retrieve the types of the table's columns and validate
    # the supplied record fields as being the right type.
        query = "SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;"
        types = msq.query(query, (self.table,)).values.tolist() # Format so we can use it
        # Flatten it
        types = tuple([v for vals in types for v in vals])
        match = {}
        for i in range(0, len(types)): # For every entry in the record
            item_type = type(record[i]) # Get the type of that part of the record (actual data)
            print("Actual data type:", item_type)
            # Get the corresponding column's type and convert to the Python 
            # equivalent for comparison
            col_type = msq.convert_to_python_type(types[i])
            print("Python type equiv:", col_type)
            if item_type != col_type:
                # TODO: SHOULD we coerce the type into the correct one if possible? 
                # (eg int -> float can be done; forcing float only is overly restrictive)
                # On the other hand, type coercion could allow invalid data if abused
                match[types[i]] = False
                print(f"Type of column {i}: {record[i]} ({item_type}) does not match database; must be {col_type}.)")
            else:
                match[types[i]] = True # Types match, good to go
        return match

    def __check_if_in_table(
            self, 
            resource_id: int
            ):
        record_exists, status = self.view_record(resource_id)
        #print(record_exists, status)
        if status != 404:
            return True
        else:
            return False
    
    # Hash a value using password standards
    # Used to protect data before it's stored in the database (passwords)
    # <- value: the value to hash
    # -> value: the value, hashed with pbkdf2.
    @staticmethod
    def hash_value(
        value: str
        ):
        hasher = a2.PasswordHasher()
        # Argon2id is used for hashing - see https://argon2-cffi.readthedocs.io/en/stable/
        value = hasher.hash(value)
        return value
    
    # Check whether an entered password matches the password in the database
    # Also rehashes the password if needed (e.g. password hash mechanism has changed)
    # Requires worker to be attached to the logins table
    # <- user_id: the id of the user to check against
    # <- password: the entered password to test
    # -> int, bool: the HTTP status code and whether the password matches
    def check_password(
            self, 
            user_id: int, 
            password: str
            ):
        hasher = a2.PasswordHasher()
        # Sanity check that we can actually get to the login table
        if self.table != "logins":
            print("Worker must be attached to logins table to verify.")
            return 500, False # Server error; API code is the problem
        # Get the hash for the specified user
        try:
            results = msq.query(f"SELECT password FROM {self.table} WHERE id = %s;", (user_id,))
            if isinstance(results, pd.DataFrame): # Ensure that we only have one row!
                # Ensure we only have one row- one password per user. Otherwise, raise an exception to complain.
                if results.shape[0] != 1:
                    raise Exception # TODO Find something more specific
                # Get the hash for the specified user
                hash = results["password"].iloc[0]
            else: # Something went wrong with our SQL query
                print("Password not found.")
                return 404, False # For now? Break this into server error vs not existing
        except Exception as ex:
            print("Could not retrieve hashed password:", ex)
        # Verify the entered password against the hash
        try:
            hasher.verify(hash, password)
            # TODO: Check if rehash is needed and rehash (then store rehashed) if necessary
            if hasher.check_needs_rehash(password):
                new_hash = hasher.hash(password)
                # TODO: also update "updated" column?
                status, updated_row = self.update_record(user_id, {"password": new_hash})
            return 200, True
        except a2.exceptions.VerifyMismatchError:
            print("Incorrect password.")
            return 401, False # User error, password is incorrect; 401? 400?
        except Exception as ex:
            print("Could not verify password:", ex)
            return 500, False # Server error
    
    # Prepare a record to be inserted into a table
    # <- id_col_name: the name of the table's ID column
    # <- resource_name: the name of the resource associated with this table; e.g. "customers".
    # Used to build API links.
    # <- request: an HTTP request from Flask.
    # -> record: a tuple containing the record with its contents formatted for the table as needed
    # TODO: there has to be a more compact way to handle special cases, right?
    def __build_record(
        self,
        id_col_name: str, # The name of the ID column for this table; used to build self links
        resource_name: str, # The corresponding resource name for this table; used to build uplinks
        request # The HTTP request; needed to get params
    ):
        #print("Formatting record")
        row = {}
        # Used to build URI and make UUID5
        upname = "/speedes/1_0/" + resource_name
        if upname[-1] != "/": # Uniform formatting, please
            upname += "/"
        # Get the id for use in other functions
        record_id = self.__request.values.get(id_col_name)
        # Build record from supplied column names, getting from request as needed
        for col in self.__table_cols:
            # The primary key column
            if col == id_col_name:
                row[col] = record_id
            # UUID column
            elif col == "uuid":
                #row[col] = uuid4()
                this_url = url + upname + str(record_id)
                row[col] = str(uuid5(NAMESPACE_URL, this_url))
            # bool columns
            elif col == "enabled":
                try:
                    bitval = bool(self.__request.values.get(col))
                    row[col] = bitval
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
                    row[col] = upname + str(record_id)
                except:
                    # For now, this works, but there's a better way that's less delicate
                    return "Columns out of order"
            elif col == "self_link_rel" and resource_name != None:
                row[col] = "self"
            # Date columns that need to be generated
            elif col == "published" or col == "updated":
                row[col] = dt.now().strftime("%Y-%m-%d %H:%M:%S")
            elif "password" in col:
                # Store as a hash, not the raw password!
                row[col] = self.hash_value(self.__request.values.get(col))
            # Other columns that need to be requested from http
            else:
                row[col] = self.__request.values.get(col)
        # Check the validity of the new record
        # Do the columns actually exist in the table?
        record = self.__check_against_columns(row)
        # Flatten the dictionary into just the values for checks on the actual record to insert
        record = tuple(record.values())
        # Are the items of the right types?
        #type_validity = self.__check_types(record)
        type_validity = (True, True) # FOR NOW. TODO finish fixing this function
        if False not in type_validity:
            return record
        else:
            # TODO: can this be handled more gracefully than just saying "nope"?
            for column in type_validity:
                if type_validity[column] == False:
                    print(f"Type of {column} invalid; cannot insert")
            return None

    # Add a new record to the table
    # Also calls checks to validate said record
    # <- record: a prepared dictionary to insert into the table
    # -> values: the newly inserted record
    # -> status: the HTTP code for the operation status
    # -> content-type for JSON returns
    def add_record(self, record: dict):
        print("Adding new record.")
        if isinstance(record, dict): # Maybe they passed us an already-formatted tuple
            record = self.__build_record(record, self.__resource_id, self.__request) # Format and validate
        if record is not None: # Validation passed
            try:
                status, values = msq.insert_MySQL(self.__table_cols, record, self.table)
            except Exception as ex:
                print("Could not insert new record:", ex)
                status = 400
            if status == "1062": # Duplicate entry for ID error
                return 400, "Duplicate ID"
            elif status in [400, 500] or values == None:
                values = "Server Error: no record inserted"
        # TODO: should sensitive values be returned in the inserted record (e.g. password hash)?
        return status, values

    # Update an existing record in the table
    # <- record_id: the ID of the record to update
    # <- new_data: the values to update in the record. May contain some or all columns of the table.
    # -> HTTP status code
    # -> Updated record
    # TODO more robust try/catch for this function
    def update_record(self, record_id: int, new_data: dict):
        print("Updating record", record_id)
        # Validate that the columns we're asking to change actually exist
        new_data = self.__check_against_columns(new_data)
        # For columns with a value of None, grab the old value from the table
        none_cols = [col for col in new_data.keys() if new_data[col] == None]
        row_id = record_id
        query = f"SELECT * FROM {self.table} WHERE {self.id_col} = %s;"
        values = msq.query(query, (row_id,))
        # Overwrite the columns listed in new_data with the new data
        for col in new_data:
            if col not in none_cols: # If this column has been supplied with new values to update to
                if "password" in col: # Hash the password column values!
                    new_data[col] = self.hash_value(new_data[col])
                values[col] = new_data[col]
        # Place the values into the table, overwriting the existing row
        query = f"UPDATE {self.table} SET "
        parameters = []
        for col in new_data:
            query += f"{col} = %s, "
            parameters.append(values[col].iloc[0])
        query = query[:-2] + " " # Remove final comma
        query += f"WHERE id = {row_id};"
        try:
            msq.query(query, parameters) # Make the change
            values = values.to_json(orient="records")
            # Get the updated record to return as per RESTful expectation
            #query = f"SELECT * FROM {self.table} WHERE id = %s;"
            #values = msq.query(query, (row_id,))
            # TODO: make sure this doesn't reveal sensitive rows!
            return 200, values # All is well; return new row to conform to API expectations
        except Exception as ex:
            print("Query failed:", ex)
            return 500, "Could not update"

    # Delete a record from the table
    # <- record_id: the ID of the record to delete
    # -> HTTP status code
    def delete_record(self, record_id: int):
        try:
            status = msq.delete_record(record_id, self.table)
            return status, f"Successfully deleted record with ID = {record_id}"
        except:
            return 500, "Server error"

    # View a single record of the table
    # <- record_id: the ID of the record to return
    # -> the record or an HTTP error code
    def view_record(self, record_id):
        try:
            table = self.table
            # TODO: don't ask for sensitive columns in the first place
            results = msq.query(f"SELECT * FROM {table} WHERE id = %s;", (record_id,))
            if isinstance(results, pd.DataFrame):
                if results.empty:
                    return 404, "Record not found" # Resource not found, does not exist
            elif str(results) == "404":
                return 404, "Record not found" # Resource not found, does not exist
        except Exception as ex:
            print("Could not retrieve table:", ex)
            return 500, "Server error"

        try:
            #results = pd.DataFrame.from_records(results)
            # Remove sensitive columns from results to avoid leaking information
            results = self.remove_sensitive_columns(results)
        except Exception as ex:
            print("Could not coerce to DataFrame or remove sensitive columns:", ex)
            return 500, "Server error"
        # Format to JSON
        if isinstance(results, pd.DataFrame):
            try:
                results = results.to_json(orient="records")
                return 200, results
            except Exception as ex:
                print("Could not coerce to JSON:", ex)
                return 200, results
        elif isinstance(results, str):
            return ("Record:", results)
        else:
            print("Cannot return record; wrong data type.")
            return 500, "Server error"
        
    # Remove sensitive information from a pandas frame for returning to the user
    # Define sensitive columns in self.__init__
    # Please also ensure that data is protected in the database itself!
    # <- data: pandas frame of data to clean
    # -> data: data with sensitive columns removed
    def remove_sensitive_columns(self, data):
        print("Cleaning sensitive columns")
        # Remove sensitive columns from results
        try:
            if isinstance(data, pd.DataFrame):
                sensitiveFilter = data.filter(self.__sensitive_columns)
                data.drop(sensitiveFilter, inplace=True, axis=1)
                return data
            else:
                print("Cannot clean columns; please format data into DataFrame first.")
                return None
        except Exception as ex:
            print("Cannot remove sensitive columns:", ex)
            return None

    # View the entire table
    # <- nothing
    # -> the table's records or an HTTP error code
    def view_table(self):
        print("Retrieving table")
        try:
            # Get the table
            results = msq.query(f"SELECT * FROM {self.table};")
        except Exception as ex:
            print("Cannot query:", ex)

        try:
            # Transform into return format if necessary; output dataframe
            results = self.adjust_formatting(results)
            # Take out any sensitive columns
            results = self.remove_sensitive_columns(results)
            print("Formatting done")
        except Exception as ex:
            print("Could not format table for return:", ex)
            return 500, "Server error"
        
        # Format to JSON
        print("Checking result existence")
        if results.empty:
            print("Table is empty")
            return 404, "Not found" # Resources not found, do not exist
        elif results is None:
            print("No results found; error likely occurred when formatting for return")
            return 500, "Server error: check console"
        else:
            print("All good, returning...")
            return 200, results.to_json(orient="records")
        
    # Make changes to output format for a given table to match frontend format expectations
    # <- data: the raw table data as a pandas frame
    # -> data: modified pandas frame of data
    def adjust_formatting(self, data):
        print("Adjusting table display for frontend")
        match self.table:
            case "retail_customers":
                try:
                    # Handle customer name -> one field
                    data["legalName"] = data["first_name"] + " " + data["last_name"]
                    del data["first_name"]
                    del data["last_name"]
                except Exception as ex:
                    print("Could not adjust name fields for retail_customers:", ex)
            case "logins":
                del data["password"] # Not returning this!
        return data
        
    # Ensure that a foreign key exists in the table that corresponds to an existing record
    # <- fk_id_value: the ID to check in the foreign table
    # <- fk_id_col: the ID column of the referenced table
    # <- fk_table: the table to check
    # -> bool: does the key exist in the FK table?
    # e.g. if Table1.fk_col references Table2.id, and this Worker is for Table1, then
    # check_foreign_key_exists(1, "id", "Table2") checks whether a record with ID = 1
    # exists in Table2. If it does, it returns True. Else, it returns False.
    def check_foreign_key_exists(self, fk_id_value, fk_id_col, fk_table):
        fk_results = msq.query(f"SELECT COUNT({fk_id_col}) FROM {fk_table} WHERE {fk_id_col} = %s;", (fk_id_value,))
        if fk_results.empty: # The ID doesn't exist yet
            print(f"400: Foreign key {fk_id_value} in {fk_table} does not exist.")
            return False
        else:
            return True
        