import pandas as pd
from scripts.sqlWorkerClass import sqlTableWorker
# Timezone conversions
from zoneinfo import ZoneInfo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta

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

def is_dst(when):
    #Given the name of Timezone will attempt determine if that timezone 
    # is in Daylight Saving Time now (DST) - see
    # https://gist.github.com/dpapathanasiou/09bd2885813038d7d3eb
    return when.dst() != timedelta(0)

# Find days where Daylight Savings kicks in for a time zone
# Edited from https://zetcode.com/python/time-daylight/
# Returns a list of datetimes where the date is a daylight savings
# transition for tz
def find_dst_transitions(
        years: list, 
        tz: str
        ):
    transitions = []
    last_dst = None
    # For each year tested...
    for year in years:
        # Check each day of the year
        delta = relativedelta(years=1)
        # Noon is to catch the DST transition! Midnight would give
        # an off by one error
        this_date = dt(year, 1, 1, 12, 0, 0, 0, tzinfo=tz)
        end_date = this_date + delta
        while this_date <= end_date:
            local_time = this_date
            current_dst = is_dst(local_time)
            if last_dst is not None and current_dst != last_dst:
                print("DST transition found by find_dst_transitions():", local_time)
                # Timedelta is so it's returned at midnight, not noon
                # to ensure time selection stays accurate
                transitions.append(local_time - timedelta(hours=12))
            last_dst = current_dst
            this_date = this_date + timedelta(days=1)
    return transitions

# Convert from UTC to local time
# tz should be a timezone in standard, full name format:
# e.g. 'America/Los_Angeles'
def convert_to_tz(data, tz):
    try:
        timezone = ZoneInfo(tz)
    except Exception as ex:
        print(f"Could not initialize time zone: {ex}")
        print("Timestamps will be in UTC or Unix Time!")
    try:
        # Convert to time zone
        # We have to define a function to take keyword arguments for .apply()
        def replace_timezone(x, **kwargs):
            for arg in kwargs:
                x = x.replace(tzinfo=kwargs[arg])
            return x
        # Make the conversion
        data["timestamp"] = data["timestamp"].apply(replace_timezone, tz=timezone)
        print("Successfully converted timestamps to provided timezone.")
    except Exception as ex:
        print(f"Unable to convert time zone: {ex}")
        print("Timestamps may be in UTC or improperly converted!")
    # Make it easier to work with the timestamp index column
    # Fix duplicate and missing hours
    # Duplicates first
    # Sum them- we don't want to lose the extra hour's power usage
    data = data.groupby("timestamp").sum()
    data = data.reset_index()
    # Get rid of the unnecessary duplicates now that their data is saved
    data = data.drop_duplicates(subset="timestamp", keep="first")

    # Deal with the missing hour- "spring forwards"
    # AKA: make sure it's NA! There shouldn't be data here
    # If there is, either make it NA or flag as questionable
    # Get list of years so we can find the transition days for those years
    start_year = data["timestamp"].iloc[0]
    end_year = data["timestamp"].iloc[-1]
    years = []
    yearrange = range(int(start_year.year), int(end_year.year) + 1)
    for year in yearrange:
        years.append(year)
    # Find DST transition dates
    transition_days = find_dst_transitions(years, timezone)
    utc = ZoneInfo("UTC")
    # TODO TEMPORARY- dynamically find the change time instead!
    starttime = "03:00"
    starttime = dt.strptime(starttime, "%H:%M").replace(tzinfo=timezone)
    endtime = "03:59" # Actual break point
    endtime = "04:16" # For convenience to see surrounding times
    endtime = dt.strptime(endtime, "%H:%M").replace(tzinfo=timezone)
    # Get the data for those dates
    data = data.set_index("timestamp")
    for date in transition_days:
        #date = dt.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone)
        start_dt = date + timedelta(hours=starttime.hour) # At starttime: add the time!
        end_dt = date + timedelta(hours=endtime.hour, minutes=endtime.minute) # At endttime: add the time!
        try:
            affected = data.loc[start_dt:end_dt]
            print(affected)
        except:
            print("Could not locate DST transition day in data;")
            print(f"From {start_dt} to {end_dt}")
        # Fix any NA entries at the transition times
        #print(data)
    data = data.reset_index()
    return data

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