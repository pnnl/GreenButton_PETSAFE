from . import mysql_database as msq
import pandas as pd

# Retrieve the metadata for a given meter
class metadataCaller:
    def __init__(
            self, 
            meter_id: int
            ):
        
        self.meter_id = meter_id
        self.__metadata = self.__query_meter()
        self.__address = self.get_address()

    # Get information associated with the meter from the
    # MySQL database
    # Address: left join addresses table
    # Other metadata:
    # usage_points?
    def __query_meter(self):
        query = "SELECT * FROM usage_points WHERE id = %s \
            LEFT JOIN addresses on usage_points.address_id=addresses.id \
            LEFT JOIN access_metadata on usage_points.id=access_metadata.meter_id;"
        metadata = msq.query(query, (self.meter_id,))
        return metadata
    
    # List the columns in a table so metadata can be filtered
    # to just that table
    def __get_columns(self, table):
        try:
            query = 'SELECT column_name FROM INFORMATION_SCHEMA.COLUMNS WHERE table_name = %s;'
            cols_in_table = tuple([v for vals in (msq.query(query, (table,)).values) for v in vals]) # Flatten list
            cols_in_table = tuple(dict.fromkeys(cols_in_table)) # Remove duplicates, keeping order
            return cols_in_table
        except Exception as ex:
            print(table, "could not be retrieved:", ex)
            return None

    # Get the results from one specific table by column matching
    def __get_table_subset(self, tablename):
        subset_cols = list(self.__get_columns(tablename))
        subset_cols.append(id)
        subset_metadata = self.__metadata.copy()
        subset_metadata = subset_metadata[subset_cols]
        return subset_metadata

    # Get the current address of the meter
    def get_address(self):
        address_metadata = self.__get_table_subset("addresses")
        return address_metadata

    # Get a given user's access permissions (with privacy level)
    # for the meter (check expiration date too)
    def get_permissions(self, customer_id):
        access_metadata = self.__get_table_subset("access_metadata")
        return access_metadata

    # Check when a user's access to the meter expires
    def get_access_expiration(self, customer_id):
        pass

    # Find out why a customer has access to a meter
    def get_share_purpose(self, customer_id):
        purpose = self.__metadata["share_purpose"]
        return purpose

    # Determine if this meter is a virtual meter
    # TODO: check that it shows up in Pandas as "1" and not 1 or True
    # (Or expand the check if any of those are possible translations of bit(1))
    def check_if_virtual_meter(self):
        virtualization_col = self.__metadata["isVirtual"]
        match virtualization_col[0]: # There should only be one entry here
            case "1": # Meter is marked as being virtual
                return True
            case __: # Meter not marked as being virtual
                return False

    # If meter is virtual, determine which meters are
    # being aggregated to create it
    def get_meters_in_virtual_meter(self):
        isVirtual = self.check_if_virtual_meter()
        if not isVirtual: # Not a virtual meter, no aggregation
            return None
        # Ask the database
        query = "SELECT * FROM virtual_meter_mappings \
            WHERE virtual_meter_id = %s;"
        component_meters = msq.query(query, (self.meter_id,))
        return component_meters["component_meter_id"].to_list()

