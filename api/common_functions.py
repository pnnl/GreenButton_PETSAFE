import pandas as pd

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
    print(address_record)
    formatted_addr = address_record["fullAddress"]
    if formatted_addr == None:
            # Format the address
            addr = {}
            addr["address"] = str(address_record["building"]) + " " + \
                                str(address_record["streetPrefix"]) + " " + \
                                str(address_record["streetNumber"]) + " " + \
                                str(address_record["streetName"]) + " " + \
                                str(address_record["streetSuffix"]) #+ " " + \
                                #str(customer_address["streetType"])+ " " + \
            addr["addressNumber"] = str(address_record["houseFractionNumber"]) + " " + \
                                    str(address_record["unit"]) + " " + \
                                    str(address_record["building"])
            addr["city"] = address_record["city"]
            addr["state"] = {"code": address_record["state"], "name": ""} # TODO: handle name lookup or store name
            addr["zip"] = str(address_record["zipCode"]) + "-" + str(address_record["zipFour"])
    return formatted_addr