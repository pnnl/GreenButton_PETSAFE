import pandas as pd
from sqlWorkerClass import sqlTableWorker

# <- d1: a dictionary. Any contents permitted.
# <- d2: a dictionary. Any contents permitted.
# -> dict: a dictionary containing the contents of both dictionaries, with any
# identical items merged (no duplicates)
# WARNING: does not handle keys with non-identical values; use at your own risk!
# TODO: handle that case
def combine_dict(d1, d2):
    return {
        k: tuple(d[k] for d in (d1, d2) if k in d)
        for k in set(d1.keys()) | set(d2.keys())
    }

# Extract all usage points whose address matches a given address.
# This should effectively list all meters at that address.
def list_component_sites(address_id):
    # Retrieve building from database
    query = "SELECT id FROM usage_points WHERE address_id == %s;"
    status, results = sqlTableWorker.run_query(query, (address_id,))
    return status, results

# Check a customer's provided token against the one stored in the MySQL database.
# IF it matches, return True.
# If it doesn't, return False.
def authenticate_token(
          submitted_token: str # The OAuth token
          ):
     # TODO: We should extract the token's customer id claim here instead
     # of asking for it, since it should be part of the claim.
     customer_id = 0 # Placeholder for extracted claim retail_customer_id
     # TODO: Work out which of these actually contain needed information
     query = "SELECT access_token, status, state, ap_start, ap_duration FROM authorizations WHERE retail_customer_id == %s;"
     status, results = sqlTableWorker.run_query(query, (customer_id,))
     # TODO: will a customer ever have more than one token? If so, should they all be considered
     # potentially valid, or should we assume something is wrong?


# <- address_record: the full address record with the following fields expected by this function
# (null/None values are acceptable):
#  `houseFractionNumber` varchar(255) DEFAULT NULL,
#  `unit` varchar(255) DEFAULT NULL, /* eg. Apt. 4 */
#  `building` varchar(255) DEFAULT NULL,
#  `streetName` varchar(255) DEFAULT NULL,
#  `streetNumber` varchar(255) DEFAULT NULL,
#  `streetPrefix` varchar(255) DEFAULT NULL, /* eg. North */
#  `streetSuffix` varchar(255) DEFAULT NULL,
 # `streetType` varchar(255) DEFAULT NULL,
 # `city` varchar(255) DEFAULT NULL,
 # `county` varchar(255) DEFAULT NULL, /* currently not implemented in this function; may be in future */
 # `state` varchar(2) DEFAULT NULL, /* 2 letter state abbreviation */
 # `zipcode` int(5) DEFAULT NULL, /* 5 digit zip code */
 # `zipFour` int(4) DEFAULT NULL, /* 4 digit extension to zip code */
 # `fullAddress` varchar(255) DEFAULT NULL, /* Full address, if provided as such */
 #
 # -> formatted_addr: a dict of strings and dicts; describes the address for use in JSON output
def build_address(address_record: pd.Series):
    # Ensure format is correct so the selection of different address parts works as intended
    if not isinstance(address_record, pd.Series) and not isinstance(address_record, pd.DataFrame):
        try:
            print("Please pass address as a Pandas DataFrame or Series object.")
            address_record = pd.DataFrame(address_record)
        except:
            print("Please pass address as a Pandas DataFrame or Series object.")
    # If we already have a full address, use that instead of trying to build one from scratch
    # (though this assumes the format of the full address is fine already- is that a safe assumption?)
    if str(address_record["fullAddress"]).strip() != "":
        formatted_addr = address_record["fullAddress"]
    else:
        # We don't have a full address field. We need to build one- the API returns
        # that field as one line if this function is invoked, meaning that all of
        # these fields need to be coerced into a single string for return
        addr = {}
        addr["address"] = format_address_component(address_record["building"]) + \
                        format_address_component(address_record["streetPrefix"]) + \
                        format_address_component(address_record["streetNumber"]) + \
                        format_address_component(address_record["streetName"]) + \
                        format_address_component(address_record["streetSuffix"]) + \
                        str(address_record["streetType"])
        addr["addressNumber"] = format_address_component(address_record["houseFractionNumber"]) + \
                                format_address_component(address_record["unit"]) + \
                                str(address_record["building"])
        addr["city"] = address_record["city"]
        #addr["state"] = {"code": address_record["state"], "name": ""} # TODO: handle name lookup or store name
        addr["zip"] = str(address_record["zipcode"]) 
        if address_record["zipFour"] != "":
            addr["zip"] = addr["zip"] + "-" + str(address_record["zipFour"])
        for component in addr:
            addr[component] = addr[component].strip()
        formatted_addr = addr["addressNumber"] + " " + addr["address"] + ", " + addr["city"] + ", " \
            + address_record["state"] + " " + addr["zip"]
    return formatted_addr

def format_address_component(component):
    component = str(component) # Ensure format matches
    if component != "": # Add spaces only if the component has content
        component = component + " "
    return component