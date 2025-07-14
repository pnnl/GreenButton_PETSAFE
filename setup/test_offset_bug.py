import pandas as pd
from zoneinfo import ZoneInfo
from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional

UTC = ZoneInfo("UTC")
local = ZoneInfo('America/Los_Angeles')


def generate_test_data():
    # Generate 15 min timestamps
    start_date = "2023-01-01"
    end_date = "2023-12-31"
    start_date = dt.strptime(start_date, '%Y-%m-%d')
    end_date = dt.strptime(end_date, '%Y-%m-%d')
    data = pd.DataFrame()
    fifteen_min_increments = pd.date_range(start=start_date, end=end_date, tz=UTC, freq="15min", normalize=True, inclusive="left")
    data["timestamp"] = fifteen_min_increments
    data = data.set_index("timestamp")
    # Generate predictable data that can be used to track any shifts
    hour = 0
    hour_repeat = 1
    for time in fifteen_min_increments:
        print(time)
        print(data.iloc[time])
        if hour_repeat == 4:
            hour += 1
            hour_repeat = 1
        data.iloc[time]["power"] = hour
        hour_repeat += 1
    # Display data for verification that it's as expected
    print(data)
    pass

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

def debug_check_conversion(
        data: pd.DataFrame, 
        timezone: str, 
        check_doubles: Optional[bool] = True
        ):
    # Check our work
    # Get list of years so we can find the transition days for those years
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
        #starttime = "03:00"
        starttime="01:00"
        starttime = dt.strptime(starttime, "%H:%M").replace(tzinfo=timezone)
        endtime = "03:59" # Actual break point
        endtime = "04:01" # For convenience to see surrounding times
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

def main():
    data = generate_test_data()

main()