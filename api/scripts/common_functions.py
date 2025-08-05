import pandas as pd
from scripts.sqlWorkerClass import sqlTableWorker
# Timezone conversions
from zoneinfo import ZoneInfo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional
from numpy import nan

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
                print("DST transition found:", local_time)
                # Timedelta is so it's returned at midnight, not noon
                # to ensure time selection stays accurate
                transitions.append(local_time - timedelta(hours=12))
            last_dst = current_dst
            this_date = this_date + timedelta(days=1)
    return transitions

# Convert from UTC to local time
# tz should be a timezone in standard, full name format:
# e.g. 'America/Los_Angeles'
# NOTE: An hour may be missing for "spring forward" daylight saving
# transitions. This hour is filled in with NAIVE timestamps that are
# implied to be in the same time zone as the aware timestamps.
# Naive stamps are used because Python libraries (sensibly) refuse
# to represent the nonexistent hour, but we still need to return it
# with NA values for graphing purposes, hence the use of naive
# timestamps to represent that time period
def convert_to_tz(data, tz):
    try:
        timezone = ZoneInfo(tz)
    except Exception as ex:
        print(f"Could not initialize time zone: {ex}")
        print("Timestamps will be in UTC or Unix Time!")
    if "timestamp" in data.columns:
        data = data.set_index("timestamp")
    try:
        # Convert to time zone
        data.index = data.index.tz_convert(tz=ZoneInfo(tz))
        print("Successfully converted timestamps to provided timezone.")
    except Exception as ex:
        print(f"Unable to convert time zone: {ex}")
        print("Timestamps may be in UTC or improperly converted!")
        return data
    # Make it easier to work with the timestamp index column
    # Fix duplicate and missing hours

    # Deal with the missing hour- "spring forwards"
    # AKA: make sure it's NA! There shouldn't be data here
    # If there is, either make it NA or flag as questionable
    # Build a new index with all timestamps
    #data = data.set_index("timestamp")
    start_datetime = data.index[0]
    end_datetime = data.index[-1] + pd.Timedelta(1, "d") # one day ahead for date_range to work properly
    # Holding for reference:
    # doubletime="2023-03-11 20:00:00-07:00"
    # doubletime = dt.strptime(doubletime, "%Y-%m-%d %H:%M:%S%z")
    # Any intervals missing not accounted for by daylight savings will be caught by this
    # and filled with numpy.NaN
    # Apologies for hardcoding the frequency
    fifteen_min_increments = pd.date_range(start=start_datetime, end=end_datetime, tz=timezone, freq="15min", inclusive="left")
    new_index = pd.Index(fifteen_min_increments, name="timestamp")
    data = data.reindex(index=new_index, method=None) # Do not impute over missing times!
    # Filling daylight savings is a bit trickier, as pd.date_range will NOT fill it
    # but we also can't rely on manually specifying the missing hour
    # Instead, we create a copy of the timestamps without the timezone info
    # to find the missing time, fill with date_range since it works on naive times, 
    # then use replace() to re-add the pre-DST time zone and fill with NA.
    # All to ensure continuity of the resulting graph.
    times = data.index.copy()
    #times = times.tz_localize(None) # Remove timezone, preserve times
    times = times.to_pydatetime() # Get into regular timezone format to ease comparison
    for value in range(0, len(times)):
        times[value] = times[value].replace(tzinfo=None)
    # Create a series of all times that SHOULD be present
    all_times = pd.Series(pd.date_range(start=times[0], end=times[-1], freq="15min", inclusive="both"))
    times = pd.Series(times)
    # Visually confirm that a known missing time DOES exist in all_times, but not times
    #testtime = dt.strptime("2023-03-12 02:00:00", "%Y-%m-%d %H:%M:%S")
    #print(all_times.loc[all_times == testtime])
    #print(times.loc[times == testtime])
    # Find rows in complete time series that are not present in times
    comparison = pd.Series(all_times.isin(times))
    missing_rows = comparison[comparison == False].index
    # Get the first time zone
    #first_time = data.index[0]
    # TODO extract the time zone
    #first_timezone = first_time.utcoffset()?
    # Add to data, using pre-DST time zone
    missing_rows_corrected = []
    for time in missing_rows:
        #missing_rows_corrected.append(all_times.iloc[time].replace(tzinfo=timezone))
        missing_rows_corrected.append(all_times.iloc[time])
    recreated_times = pd.DataFrame()
    recreated_times["timestamp"] = missing_rows_corrected
    recreated_times["meter_id"] = data["meter_id"].iloc[0]
    recreated_times["real_power"] = nan # No readings here
    recreated_times = recreated_times.set_index("timestamp")
    # We need to insert these records in the correct location for them to return-
    # we can't use sort because pandas refuses to compare naive and aware datetimes.
    # What we can do is slice the data before the time to add, add it in,
    # and re-add the back half of the data.
    # First, get the last time before the break point.
    # Append to the data frame
    data = pd.concat([data, recreated_times])

    # Check our work
    #debug_check_conversion(data, timezone, False)

    if "index" not in data.columns: 
        data = data.reset_index() # Ensures JSON output includes timestamp
    return data

# Can be called to check that the time zone is correct by viewing
# the times around daylight savings
def debug_check_conversion(
        data: pd.DataFrame, 
        timezone: str, 
        check_doubles: Optional[bool] = True
        ):
    # Check our work
    # Get list of years so we can find the transition days for those years
    if "timestamp" not in data.columns:
        data = data.reset_index()
    start_year = data["timestamp"].iloc[0]
    end_year = data["timestamp"].iloc[-1]
    years = []
    yearrange = range(int(start_year.year), int(end_year.year) + 1)
    for year in yearrange:
        years.append(year)
    # Find DST transition dates
    transition_days = find_dst_transitions(years, timezone)
    # Check the time where things tend to be duplicated
    if check_doubles:
        # Ensure we can find a specific time
        if "timestamp" in data.columns:
            data = data.set_index("timestamp")
        # Find that time
        doubletime="03:00"
        doubletime = dt.strptime(doubletime, "%H:%M").replace(tzinfo=timezone)
        for date in transition_days:
            double_datetime = date + timedelta(hours=doubletime.hour)
            try:
                print(data.loc[double_datetime])
            except KeyError:
                print(double_datetime, "not found")
    else:
        # Check regular DST transition times
        starttime="01:00"
        starttime = dt.strptime(starttime, "%H:%M").replace(tzinfo=timezone)
        endtime = "04:00"
        endtime = dt.strptime(endtime, "%H:%M").replace(tzinfo=timezone)
        # Get the data for those dates
        data = data.set_index("timestamp")
        for date in transition_days:
            #date = dt.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone)
            start_dt = date + timedelta(hours=starttime.hour) # At starttime: add the time!
            end_dt = date + timedelta(hours=endtime.hour, minutes=endtime.minute) # At endttime: add the time!
            try:
                #nstart = dt.strptime("2023-03-12 00:00", "%Y-%m-%d %H:%M")
                affected = data.loc[start_dt:end_dt]
                print(affected)
                #print(data.between_time("1:00", "4:00"))
            except KeyError as ex:
                print("Requested time period not found in data:", ex)
                print(f"From {start_dt} to {end_dt}")
            except Exception as ex:
                print("Could not locate DST transition day in data:", ex)

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