from fitter import Fitter
import scipy
import multiprocessing as mp
from math import floor
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas import read_csv

# Parameters for curve
# pareto: (0.5335371308758773, -0.16241563710448093, 2.1624156371044805)
dist_c = 2.5335371308758773
dist_loc = -0.16241563710448093
dist_scale = 2.1624156371044805

# levy
dist_loc = 1.364779244088083
dist_scale = 2.5963880878956456

# halfcauchy
dist_loc = 2
dist_scale = 2.1624533028540704

def get_nums_wrapper():
    nums = []
    number_of_measurements = 1000 #2000000 # 341
    max_size_limit = 50000
    min_size_limit = 2
    for i in range(0, number_of_measurements): # number of measurements to take
        nums.append(get_num(min_size_limit, max_size_limit))
    nums = pd.array(nums)
    numcounts = nums.value_counts()
    numcounts = numcounts / number_of_measurements # Convert to percentage of the time it was chosen
    return numcounts

def get_num(min, max):
    num = -1 # Intentionally invalid starting value for while loop
    while num < min or num > max:
        #num = int(scipy.stats.pareto.rvs(dist_c, loc=dist_loc, scale=dist_scale, size=1)[0])
        #num = int(scipy.stats.levy.rvs(loc=dist_loc, scale=dist_scale, size=1)[0])
        num = int(scipy.stats.halfcauchy.rvs(loc=dist_loc, scale=dist_scale, size=1)[0])
    return num

def expand_data_into_list(args):
    index = args[0]
    data = args[1]
    try: # this is slow. parallelize?
        print("Processing building size", index)
        countframe = data[data["BuildingSize"] == index] # grab the row for that building size
        count = int(countframe["Count"].iloc[0]) # how many of the building
        listnum = [int(index)] # the building size
        expanded = listnum * count
        expanded = pd.Series(expanded)
        return expanded
    except Exception as error:
        print("No index:", index)
        print(error)

# Get the data in original form for fitting- duplicate values and all.
def get_original_data(data):
    print("Preparing data for fitting (may take a while for large sets)...")
    #actual_data = pd.Series()
    indices = pd.unique(data.index)
    data = data.reset_index()

    processors = mp.cpu_count()
    PORTION_OF_CPU = 0.5
    processors = floor(processors * PORTION_OF_CPU)
    results = []
    args = []
    for index in indices:
        args.append([index, data])
    with mp.Pool(processes=processors) as pool:
        for result in pool.map(expand_data_into_list, args):
            results.append(result)
    actual_data = pd.concat(results)
    #print("Actual data:", actual_data)
    return actual_data

def fit_with_fitter(data):
    actual_data = get_original_data(data)
    # Using fitter library to find best fit with params
    fitter = Fitter(actual_data, timeout=120) # This WILL be painfully demanding for large sets
    fitter.distributions = ["cauchy", "alpha", "chi", "halfcauchy", "wald", "invgamma", "exponential", "pareto", "nct", "levy"]
    fitter.fit()
    summary = fitter.summary()
    print("-------")
    print(summary)
    print(fitter.get_best())
    print(fitter.fitted_param["pareto"])

# Results before adding large buildings:
#             sumsquare_error          aic          bic  kl_div  ks_statistic     ks_pvalue
# lomax             0.000146  1644.025381  1655.521029     inf      0.155425  1.165421e-07
# genpareto         0.000146  1644.025778  1655.521426     inf      0.155425  1.165421e-07
# pareto            0.000146  1644.027669  1655.523316     inf      0.155425  1.165421e-07
# levy              0.000148  1650.078976  1657.742741     inf      0.144518  1.116687e-06
# nct               0.000150  1647.454892  1662.782422     inf      0.124782  4.363519e-05
# Recommended params for best fit:
# {'lomax': {'c': 0.5335113173075132, 'loc': 1.999999999569653, 'scale': 2.16217857286271}}
# pareto: (c=0.5335371308758773, loc=-0.16241563710448093, scale=2.1624156371044805)
# levy: loc=1.364779244088083, scale=2.5963880878956456

# Results after adding large buildings (not full scale):
# cauchy, alpha, chi, halfcauchy, pareto, wald, invgamma
#             sumsquare_error          aic          bic  kl_div  ks_statistic  ks_pvalue
# halfcauchy         0.000092  1981.680633  2006.038041     inf      0.219451        0.0
# pareto             0.000122  1835.208395  1871.744507     inf      0.155423        0.0
# alpha              0.000139  2098.525795  2135.061907     inf      0.252226        0.0
# invgamma           0.000221  1827.786670  1864.322782     inf      0.148105        0.0
# cauchy             0.000312  2121.923288  2146.280696     inf      0.329187        0.0
# {'halfcauchy': {'loc': 2, 'scale': 9.060033922652938}}

def goodness_fit_test(data):
    # Test goodness of fit
    actual_data = get_original_data(data)
    #dist = scipy.stats.pareto
    #dist = scipy.stats.levy
    dist = scipy.stats.halfcauchy
    fit = scipy.stats.goodness_of_fit(dist, actual_data)
    print(fit)

def fit_data(data):
    # Test goodness of fit
    actual_data = get_original_data(data)
    dist = scipy.stats.halfcauchy

    print("Binning...")
    hist, bin_borders = np.histogram(actual_data, bins='fd', range=(2,actual_data.max()))
    bin_centers = bin_borders[:-1] + np.diff(bin_borders) / 2
    print(hist)

    print("Fitting...")
    fit = scipy.stats.fit(dist, hist) # , p0=[1., 0., 1.]

    #x_interval_for_fit = np.linspace(bin_borders[0], bin_borders[-1], 10000)
    #plt.plot(x_interval_for_fit, gaussian(x_interval_for_fit, *popt), label='fit')
    #plt.legend()
    
    #fit = scipy.stats.fit(dist, actual_data)
    print(fit)

def test_visually(data):
    # Test fit of data visually
    # Fill missing sizes
    indices = pd.unique(data.index)
    max = indices[-1]
    index = range(0, max)
    data = data.reset_index()
    index = pd.Index(index, name="BuildingSize")
    data = data.set_index(["BuildingSize"]).reindex(index)

    # Get initial frame
    numcounts = pd.Series(get_nums_wrapper())
    countFrame = data
    countFrame = countFrame.fillna(0)
    countFrame = countFrame.rename(columns={"Count": "Actual"})
    countFrame["Actual"] = countFrame["Actual"] / countFrame["Actual"].sum() # Resize to proportion of data w/that size
    print("Sum of actual:", countFrame["Actual"].sum())

    # More copies to see range
    line_count = 30 # 4
    for i in range(1, line_count + 1):
        numcounts = pd.Series(get_nums_wrapper())
        countFrame["Simulated " + str(i)] = numcounts
        print("Simulated curve", i, "done.")
    countFrame.sort_index(inplace=True)
    countFrame = countFrame.fillna(0)
    print(countFrame)
    print("Actual count:", data["Count"].sum()) # For sampling reference
    # Graph it
    fig = px.line(countFrame, labels={
        "value": "Percentage of buildings with size", 
        "BuildingSize": "Building Size"})
    max_x_axis_width = 50
    #fig.update_xaxes(autorangeoptions=dict(maxallowed=max_x_axis_width))
    fig.update_traces(opacity=0.75)
    fig.show()


def main():
    # Get the data and index

    # Set: 2022 NEEA RSBA; WA, OR, ID (NEEA)
    with open("./building-size-distribution.csv", "r") as file:
        neea_data = read_csv(file, index_col="BuildingSize")

    # Set: 2024 Open Energy Data Initiative NREL PDS building stock end use load profiles
    # https://www.nrel.gov/buildings/end-use-load-profiles.html
    with open("./multifamily-homes-by-size.csv", "r") as file:
        nrel_data = read_csv(file, index_col="BuildingID")
    nrel_data = nrel_data[nrel_data["BuildingSize"] > 1]
    nrel_data_sizes = nrel_data["BuildingSize"].value_counts() # TODO: there are weights to factor in!
    #print(nrel_data_sizes)

    # Set: 2020? HUD multifamily properties
    with open("./MULTIFAMILY_PROPERTIES_ASSISTED.csv", "r", encoding="UTF-8") as file:
        hud_data = read_csv(file)
    hud_data = hud_data["TOTAL_UNIT_COUNT"]
    hud_counts = hud_data.value_counts().sort_index()
    hud_counts = pd.DataFrame(data=hud_counts)
    hud_counts = hud_counts.reset_index()
    hud_counts = hud_counts.rename(columns={"TOTAL_UNIT_COUNT": "BuildingSize", "count": "Count"})
    hud_counts = hud_counts[hud_counts["BuildingSize"] > 1].set_index("BuildingSize") # Remove 1 and 0 unit counts
    #print("HUD counts:", hud_counts)

    # Misc (https://www.cbsnews.com/media/10-of-the-tallest-residential-buildings-in-the-u-s/)
    # confirmed with other sources:
    # New York by Gehry, NY: 904 apartments
    # John Hancock Center, Chicago: 700 condos
    # 70 Pine Street, NY: 644 apartments
    # Brooklyn Tower, NY: 150 condos, 425 apartments = 575 units
    # Metropolis Condominium, Atlanta Georgia: 498 units
    # In plans (check if carried out): Baltimore Harborplace, ML: 900+ apartments
    manual_additions = [
        [904, 1],
        [700, 1],
        [644, 1],
        [575, 1],
        [498, 1]
    ]
    outliers = pd.DataFrame(data=manual_additions)
    outliers = outliers.rename(columns={0: "BuildingSize", 1: "Count"})
    outliers = outliers.set_index("BuildingSize")
    # For now; add the nrel in future for better sample
    data = neea_data

    # Total count from census annual estimates of housing units for US in 2022
    # PROBLEM: scale is too big for fitting!
    buildings_in_us = 143789637
    buildings_in_sample = data["Count"].sum()
    size_weight = int(buildings_in_us / buildings_in_sample)
    # TODO: weight based on proportion per size- you have that data for ranges. Problem: "50+"
    data["Count"] = data["Count"] * size_weight # scale up to approximate actual proportions
    data = data.fillna(0)
    # Concat outliers into frame- done after weight because these buildings are very rare
    data = data.add(outliers, fill_value=0)
    data = data.add(hud_counts, fill_value=0)
    data = data.reindex() # Outliers get added with odd indices. This should fix that.
    #data["Count"] = data["Count"] / 10 # size is too large for scipy. Reduce it, but not so much that large buildings disappear.

    #fit_with_fitter(data)
    #test_visually(data)
    #goodness_fit_test()

    fit_data(data)

"""
 Generate random numbers:
    >>> r = expon.rvs(size=1000)

rv = expon()
    >>> ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')

ax.plot(x, expon.pdf(x),
    ...        'r-', lw=5, alpha=0.6, label='expon pdf')
"""

# Thanks, multiprocessing
if __name__ == '__main__':
    mp.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Stopping.")