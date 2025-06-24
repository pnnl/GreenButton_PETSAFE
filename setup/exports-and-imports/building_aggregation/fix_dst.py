import pandas as pd
import config
from datetime import datetime, timedelta
from list_files import list_files_in_dir
from numpy import nan

# Thanks to Daylight Savings Time, we'll have one duplicate hour and one missing hour.
# Deal with the duplicate hour by removing the second copy of it.
# Deal with the missing hour by ensuring we've imputed NA back into it.
# Save the results.
def read_json(directory):
    json_files = list_files_in_dir(directory, True)
    dsts = find_second_sundays()
    for file in json_files:
        # Retrieve JSON data
        if "metadata" not in file:
            with open(file) as open_file:
                #readings = json.load(open_file)
                readings = pd.read_json(open_file)
            # Apply DST fixes
            # First, find DST items.
            # Find duplicates and remove the second copy.
            readings = fix_duplicate_hours(readings)
            # Find the "missing hour" of March's DST and set to NA
            readings.set_index("timestamp", inplace=True)
            readings = fix_missing_hour(readings)
            # Save fixed data to new file (just in case!)
            with open(file[:-5] + "-fixedDST.json", "w") as outfile:
                readings = readings.reset_index()
                readings.to_json(outfile, indent=4, orient='records')

def fix_missing_hour(building):
    # Deal with the missing hour- find and set to NA.
    dsts = find_second_sundays()
    starttime = "02:00"
    starttime = datetime.strptime(starttime, "%H:%M")
    endtime = "02:59"
    endtime = datetime.strptime(endtime, "%H:%M")
    for date in dsts:
        # Find the hour range affected by the DST transition
        start_dt = date + timedelta(hours=starttime.hour) # At starttime: add the time!
        end_dt = date + timedelta(hours=endtime.hour, minutes=endtime.minute) # At endttime: add the time!
        # Get the data affected by DST transition
        # Set it to NA; the hour didn't exist that day
        building.loc[start_dt:end_dt] = nan
        #print(building.loc[start_dt:end_dt])
    return building

# Keep the first instance of any duplicate timestamps. Drop the others.
# Handles "fall back", albeit with loss of the duplicate hour-
# still searching for a better way to handle that
# (Have seen storing UTC + timezone + DST status; would add 2 fields but might work)
def fix_duplicate_hours(building):
    # Find duplicates
    # Sum them- we don't want to lose the extra hour's power usage
    building = building.groupby("timestamp").sum()
    # Fix power factor
    building["pf"] = building ["real_power"] / building["apparent_power"]
    # Send back the results
    building = building.reset_index()
    print(building)
    return building.drop_duplicates(subset="timestamp", keep="first")

def find_second_sundays():
    # Find DST day.
    # Second Sundays...
    # TODO: change to check from file's date range instead
    second_sundays = pd.date_range(config.START_DATE, config.END_DATE, freq="WOM-2SUN").to_series()
    # In March. Second Sundays where month == March.
    dsts = []
    for day in second_sundays:
        if day.month == 3:
            dsts.append(day)
    # DST transition days located.
    #print(dsts)
    return dsts

read_json("output/building-month-slices/year")
#data = make_fake_data()
#fix_duplicate_hours(data)