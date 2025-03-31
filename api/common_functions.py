import pandas as pd

def combine_dict(d1, d2):
    return {
        k: tuple(d[k] for d in (d1, d2) if k in d)
        for k in set(d1.keys()) | set(d2.keys())
    }

def build_address(address_record: pd.Series):
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