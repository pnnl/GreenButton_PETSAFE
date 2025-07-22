import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import box
from datetime import datetime, timedelta, time
import os
from os.path import exists
from zoneinfo import ZoneInfo
from suncalc import get_times
import pickle
 
 
# Step 1: Load Shape Files for Oregon, Washington, and Idaho
# ne_10m_admin_1_states_provinces.shp
def load_shape_files():
    print("Reading shape file.")
    # Replace with paths to your state shape files
    states_file = gpd.read_file('/mnt/hgfs/tl_2024_us_state/tl_2024_us_state.shp')
 
    # Filter for Oregon, Washington, and Idaho
    states = states_file[states_file['NAME'].isin(['Oregon', 'Washington', 'Idaho'])]
    return states
 
 
# Step 2: Create 10×10 km Grid Blocks
def create_grid_blocks(states):
    grid_blocks = []
    print("Building state grids.")
 
    for _, state in states.iterrows():
        bounds = state.geometry.bounds  # Bounds: (minx, miny, maxx, maxy)
 
        # Generate 10×10 km grid blocks
        spacing = 0.1  # Use decimal degrees equivalent to ~10 km (adjust for accuracy)
        x_coords = np.arange(bounds[0], bounds[2], spacing)
        y_coords = np.arange(bounds[1], bounds[3], spacing)
 
        for x in x_coords:
            for y in y_coords:
                block = box(x, y, x + spacing, y + spacing)
                if block.intersects(state.geometry):  # Only include blocks within state boundaries
                    grid_blocks.append({'geometry': block, 'state': state['NAME']})
 
    # Convert grid blocks to GeoDataFrame
    grid_gdf = gpd.GeoDataFrame(grid_blocks, crs=states.crs)
    return grid_gdf
 
# Step 3: Calculate Sunrise/Sunset for Each Grid Cell
def calculate_solar_times(grid_gdf, year_range):
    if not exists("solar-times.pkl"):
        UTC = ZoneInfo("UTC")
        print("Building sunrise/sunset/noon times (may take a while).")
        # Calculate daily sunrise, sunset, and solar noon times for each grid block
        for _, grid in grid_gdf.iterrows():
            centroid = grid['geometry'].centroid
            lat, lon = centroid.y, centroid.x
            print("Calculating grid_id", grid.name)
 
            # Loop through each year and day to calculate sunrise/sunset times
            dates = pd.Series()
            solar_times = pd.DataFrame()
            for year in year_range:
                year_solar_times = pd.DataFrame()
                for day_of_year in range(1, 366):
                    date = datetime(year, 1, 1, tzinfo=UTC) + timedelta(days=day_of_year - 1)
                    series_date = pd.Series(date)
                    if not dates.empty:
                        dates = pd.concat([dates, series_date])
                    else:
                        dates = series_date
                time_info = pd.DataFrame(dates)
                time_info["lon"] = lon
                time_info["lat"] = lat
                try: # Returns sunrise/set time in UTC
                    times = pd.DataFrame(get_times(dates, time_info["lon"], time_info["lat"]))
                    sunrise = times['sunrise']
                    sunset = times['sunset']
                    solar_noon = times['solar_noon']
                    #daylength = (sunset - sunrise).total_seconds()
                except Exception as ex:
                    print("Error:", ex)
                    # Skip invalid times (e.g., polar night)
                    sunrise, sunset, solar_noon = None, None, None
                year_solar_times["sunrise"] = sunrise
                year_solar_times["noon"] = solar_noon
                year_solar_times["sunset"] = sunset
                year_solar_times["daylength"] = sunset - sunrise
                year_solar_times["date"] = date.date
                year_solar_times["grid_id"] = grid.name
                year_solar_times["lat"] = lat
                year_solar_times["lon"] = lon
                solar_times = pd.concat([solar_times, year_solar_times])
                # Save as pickle to save time later
                solar_times.to_pickle("solar-times.pkl")
    else:
        with open("solar-times.pkl", "rb") as file:
            solar_times = pickle.load(file)
    return solar_times
 
def read_csv(readings_dir):
    if not exists("solar-meter.pkl"):
        data = pd.DataFrame()
        iterator = 1
        read_every_n_files = 7
        for item in os.listdir(readings_dir):
            fullPath = os.path.join(readings_dir, item)
            if os.path.isfile(fullPath) and iterator % read_every_n_files == 0:
                print("Reading", item)
                dayreadings = pd.read_csv(fullPath)
                data = pd.concat([data, dayreadings])
                iterator = 1
            else:
                iterator += 1
        data.to_pickle("solar-meter.pkl")
    else:
        with open("solar-meter.pkl", "rb") as picklefile:
            data = pickle.load(picklefile)
    return data
 
# Step 4: Load Solar Generation Data and Correlate with Grid Metadata
def find_hotspot_for_solar_generation(grid_metadata, solar_data):
    print("Retrieving readings (may take a minute on first run for large time periods).")
    # Load your solar generation measurements (ensure they have timestamps and lat/lon information)
    year = 2023
    data = read_csv(f"/mnt/hgfs/{year}-Full_v8.1/{year}/power/")
    # Or load one file- farther from equinox is best, so we're using summer solstice
    # See https://dl.acm.org/doi/pdf/10.1145/2993422.2993573
    #data = pd.read_csv(f"/mnt/hgfs/{year}-Full_v8.1/{year}/power/power-fifteen-20230621.csv")
    print("Retrieved. Narrowing to selected solar meter.")
    #month = "03"
    #day = "20" # Solar equinox
    #filepath = f"/mnt/hgfs/{year}-Full_v8.1/{year}/power/power-fifteen-{year}{month}{day}.csv"
    #data = pd.read_csv(filepath)
    # We need a site with a solar-only meter. This one is in Oregon.
    site = 521
    circuit = "CIRCUIT_27"
    # Another one!
    #site = 727
    #circuit = "CIRCUIT_13"
    solar = data.loc[(data["regname"] == circuit) & (data["ee_site_id"] == site)].copy()
    solar["min_t"] = pd.to_datetime(solar['min_t'], format="ISO8601")

    solar_generation = solar.rename({"min_t": "timestamp"}, axis=1)

    solar_generation["date"] = solar_generation["timestamp"].apply(datetime.date)

    #print(solar_generation)
    print("Done. Matching...")

    # Find solar noon for longitude calculation (estimate- imperfect system mean this may be off by a few minutes)
    # More negative = better generation
    meter_noons = pd.DataFrame()
    meter_daylengths = pd.DataFrame()
    for date in solar_generation["date"].unique():
        solar_on_date = solar_generation.loc[solar_generation["date"] == date]
        solar_noon_val = solar_on_date["power"].min() # More generation = less consumption
        meter_solar_noon_time = solar_on_date.loc[solar_on_date["power"] == solar_noon_val]#["timestamp"].iloc[0]
        #print("Noon observed:", meter_solar_noon_time)
        meter_noons = pd.concat([meter_noons, meter_solar_noon_time])
        # Find day length for latitude calculation
        # First and last instance of maximum bookend the night length; (last - first) should give day length
        # First and last instance
        # TODO: some meters have a non-zero maximum (non-generation) threshold. Refine this.
        no_gen_threshold = 0
        zero_gen_times = solar_on_date.loc[solar_on_date["power"] > no_gen_threshold]
        no_gen_start = zero_gen_times.iloc[0]["timestamp"]
        no_gen_end = zero_gen_times.iloc[-1]["timestamp"]
        # Difference
        daylength = (no_gen_end - no_gen_start).total_seconds()
        # Build the record for this date and add to frame for later use
        record = pd.DataFrame()
        record["date"] = date
        record["daylength"] = daylength
        if meter_daylengths.empty:
            meter_daylengths = record
        else:
            meter_daylengths = pd.concat[meter_daylengths, record]

    # If checking a single day, find the closest location for longitude
    #min_pos, min_diff = min(enumerate(solar_data["noon"]), key=lambda t: abs(meter_solar_noon_time - t[1]))
    #print("Closest:", min_diff)
    #print("At index:", min_pos)
    #grid_id = solar_data.iloc[min_pos]["grid_id"]

    # If checking multiple days, 
    # Build a frame of upper bounds for each location
    pass
    # Match closest bound to the ground truth's upper bound

    # If checking multiple days, match against the upper bound for latitude
    # Build a frame of upper bounds for each location
    upper_bound_daylength = pd.DataFrame()
    for location in solar_data["grid_id"]:
        loc_data = solar_data.loc[solar_data["grid_id"] == location]
        loc_max = loc_data["daylength"].max()
        loc_max_record = loc_data.loc[loc_data["daylength"] == loc_max]
        upper_bound_daylength = pd.concat([upper_bound_daylength, loc_max_record])
    print(upper_bound_daylength)
    # Match closest bound to the ground truth's upper bound



    #print("Best:", best)
    #print("Best diff:", best_diff)
    #print("Meter solar noon:", local_solar_noon)
    #grid_id = best["grid_id"]
    print("Visualizing...")
    raise SystemExit
 
    # Correlate generation measurements with grid blocks (based on lat/lon proximity)
    hotspots = []

    # Find closest region of solar noon

    # Compute the day length of the solar data- note that this implementation is
    # naive and therefore less precise- there are ways to reduce error but we're just
    # looking for a quick estimate right now
    # If the day length is closer than the previous block, save it
 
    for _, solar_row in solar_generation.iterrows():

        # TODO the problem chunk- we don't HAVE lat/long
        # The location the measurement was taken
        #measurement_point = Point(solar_row['lon'], solar_row['lat'])
        # Find where that location is on the grid
        #grid_block = grid_metadata[grid_metadata.intersects(measurement_point)]
        # If it is on our shape map grid, mark the id as its location
        #if not grid_block.empty:
            #grid_id = grid_block.iloc[0].name # Also a problem because of the above

        # TODO temp to make sure the rest of the script works! It does.
        # This is the part that's broken.
        grid_id = solar_row['ee_site_id']

        hotspots.append({
            # TODO: We don't have grid_id either.
                'grid_id': grid_id,
                'timestamp': solar_row['timestamp'],
                'generation': solar_row['power']
        })
 
    return pd.DataFrame(hotspots)
 
 
# Step 5: Plot the Grid Blocks, States, and Hotspots
def plot_grid_and_hotspots(states, grid_gdf, hot_spots):
    fig, ax = plt.subplots(figsize=(12, 12))
 
    # Plot states boundaries
    states.boundary.plot(ax=ax, color='black', linewidth=0.5)
 
    # Plot grid blocks
    grid_gdf.plot(ax=ax, color='blue', alpha=0.1)
 
    # Plot hotspots
    if not hot_spots.empty:
        # TODO Plotting them in the wrong state!
        # For each grid_id in hot_spots, find the corresponding row in grid_gdf using the grid_id column
        # ...using information we don't have. This NEEDS grid_id, which is what we're trying to find in the first place.
        hot_spots_geometry = [grid_gdf.loc[grid_id].geometry.centroid for grid_id in hot_spots['grid_id']]

        hotspots_gdf = gpd.GeoDataFrame(geometry=hot_spots_geometry, crs=grid_gdf.crs)
        hotspots_gdf.plot(ax=ax, color='red', markersize=5)
 
    plt.title("Pacific Northwest Grid Blocks and Solar Generation Hotspots")
    plt.show()
 
 
# Main Program Execution
if __name__ == "__main__":
    # Load state shape files
    pnw_states = load_shape_files()
 
    # Create grid blocks
    grid_blocks = create_grid_blocks(pnw_states)
 
    # Define year range
    years = range(2023, 2024)
    years = [2023]
 
    # Calculate sunrise/sunset times for grid blocks
    solar_times = calculate_solar_times(grid_blocks, years)
 
    # Load solar generation measurements and correlate with grid blocks
    hot_spots = find_hotspot_for_solar_generation(grid_blocks, solar_times)
 
    # Plot grid blocks, state boundaries, and hotspots
    plot_grid_and_hotspots(pnw_states, grid_blocks, hot_spots)