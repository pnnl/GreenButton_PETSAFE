import pandas as pd
from pandas import read_csv
from os.path import exists
from os import makedirs
import plotly.express as px

def bin_data(data):
    bin_interval = 100 # Large buildings bin size
    split_point = 201 # Where to switch to larger bins
    small_bins = list(range(1, split_point)) # Bin each small building size into its own bin
    large_bins = list(range(split_point, data.max() + 1, bin_interval))
    bins = small_bins + large_bins
    return bins

def adjust_bins(fig):
    fig.update_traces(xbins=dict( # bins used for histogram
        start=0.0,
        end=60.0,
        size=2
    ))
    return fig

def fill_missing(data):
                 # Fill missing sizes
    indices = pd.unique(data.index)
    max = int(indices[-1] + 1)
    index = range(0, max)
    data = data.reset_index()
    index = pd.Index(index, name="BuildingSize")
    data = data.set_index(["BuildingSize"]).reindex(index).fillna(0)
    return data

def weight_data(data):
    buildings_in_us = 143789637
    buildings_in_sample = data["Count"].sum()
    size_weight = buildings_in_us / buildings_in_sample
    return data["Count"] * size_weight

# Set: 2022 NEEA RSBA; WA, OR, ID (NEEA)
with open("data/datasets/building-size-distribution.csv", "r") as file:
    neea_data = read_csv(file, index_col="BuildingSize")

neea_data_scaled = neea_data.copy()
neea_data_scaled["Count"] = weight_data(neea_data)

# Set: 2020? HUD multifamily properties
with open("data/datasets/MULTIFAMILY_PROPERTIES_ASSISTED.csv", "r", encoding="UTF-8") as file:
    hud_data = read_csv(file)
hud_data = hud_data["TOTAL_UNIT_COUNT"]
hud_counts = hud_data.value_counts().sort_index()
hud_counts = pd.DataFrame(data=hud_counts).reset_index()
hud_counts = hud_counts.rename(columns={"TOTAL_UNIT_COUNT": "BuildingSize", "count": "Count"})
hud_counts = hud_counts[hud_counts["BuildingSize"] > 1].set_index("BuildingSize") # Remove 1 and 0 unit counts

hud_data_scaled = hud_counts.copy()
hud_data_scaled["Count"] = weight_data(hud_counts)



# Graph NEEA
#neea_bins = bin_data(neea_data)
#neea_data = pd.DataFrame(fill_missing(neea_data))
neea_data = fill_missing(neea_data)
neea_data = pd.DataFrame(neea_data).reset_index()
#print(neea_data)
neea_fig = px.histogram(neea_data, nbins=100, x="BuildingSize", y="Count", \
                        title="NEEA Buildings by Unit Count, Bin Size=4", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"})
#neea_fig.show()

# Small buildings in NEEA, more detail
mini_neea = neea_data.iloc[:50]
mini_neea_fig = px.bar(mini_neea, x="BuildingSize", y="Count", \
                       title="NEEA Buildings by Unit Count: Small Buildings", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"}) #, x="BuildingSize", y="Count"
#mini_neea_fig.show()

# Graph HUD
#hud_bins = bin_data(hud_counts)
#print(hud_counts)
hud_counts = fill_missing(hud_counts)
hud_counts = pd.DataFrame(hud_counts).reset_index()
hud_fig = px.histogram(hud_counts, nbins=200, x="BuildingSize", y="Count", \
                       title="HUD Buildings by Unit Count, Bin Size=50", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"}) #, x="BuildingSize", y="Count"
#hud_fig.show()

# Small buildings in HUD, more detail
mini_hud = hud_counts.iloc[:50]
mini_hud_fig = px.bar(mini_hud, x="BuildingSize", y="Count", \
                       title="HUD Buildings by Unit Count: Small Buildings", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"}) #, x="BuildingSize", y="Count"
#mini_hud_fig.show()

# Small to moderate buildings in HUD, more detail: 1-500
moderate_hud = hud_counts.iloc[:500]
moderate_hud_fig = px.histogram(moderate_hud, x="BuildingSize", y="Count", nbins=50, \
                       title="HUD Buildings by Unit Count: Small Buildings, Bin Size=10", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"}) #, x="BuildingSize", y="Count"
#mini_hud_fig.show()

# Graph both combined
# Combine them
#combined_data = neea_data.add(hud_counts, fill_value=0)
combined_data = neea_data
combined_data["Count"] = hud_data_scaled["Count"] + neea_data_scaled["Count"]
#combined_bins = bin_data(combined_data)
#print(combined_data)
combined_fig = px.histogram(combined_data, nbins=100, x="BuildingSize", y="Count", \
                        title="Buildings by Unit Count in Combined HUD and NEEA Datasets, Bin Size=4", \
                      labels={"BuildingSize": "Units in Building", "value": "Number of Buildings"})
#combined_fig.show()

# Small buildings in HUD, more detail
mini_combined = combined_data.iloc[:50]
mini_combined_fig = px.bar(mini_combined, x="BuildingSize", y="Count", \
                       title="NEEA and HUD Buildings by Unit Count: Small Buildings", labels={"BuildingSize": "Units in Building", "Count": "Number of Buildings"}) #, x="BuildingSize", y="Count"
#mini_combined_fig.show()

save_dir = "data/graphs/building-stock-distribution/"
save_images = True
if save_images == True:
    if not exists(save_dir):
        makedirs(save_dir)
    neea_fig.write_html(save_dir + "neea.html")
    mini_neea_fig.write_html(save_dir + "neea-small-buildings-only.html")
    hud_fig.write_html(save_dir + "hud.html")
    mini_hud_fig.write_html(save_dir + "hud-small-buildings-only.html")
    moderate_hud_fig.write_html(save_dir + "hud-size-2-to-500.html")
    combined_fig.write_html(save_dir + "combined-neea-hud.html")
    mini_combined_fig.write_html(save_dir + "combined-small-buildings-only.html")