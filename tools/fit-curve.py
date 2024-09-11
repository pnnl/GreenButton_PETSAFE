from fitter import Fitter
import scipy
import multiprocessing as mp
from math import floor
import plotly.express as px
import numpy as np
import pandas as pd
from pandas import read_csv
import decimal

def get_nums_wrapper(dist, sample_per_curve, args):
    nums = []
    number_of_measurements = sample_per_curve #2000000 # 341
    max_size_limit = 50000
    min_size_limit = 2
    for i in range(0, number_of_measurements): # number of measurements to take
        nums.append(get_num(min_size_limit, max_size_limit, dist, args))
    nums = pd.array(nums)
    numcounts = nums.value_counts()
    numcounts = numcounts / number_of_measurements # Convert to percentage of the time it was chosen
    return numcounts

def get_num(min, max, dist, args):
    loc1 = args[0]
    #loc2 = args[1]
    scale1 = args[2]
    #scale2 = args[3]
    num = -1 # Intentionally invalid starting value for while loop
    attempts = 0 # Limit how many tries can be done in case we wind up stuck with invalid values
    while num < min or num > max:
        num = int(dist.rvs(loc1=loc1, scale1=scale1, size=1)[0])
        attempts += 1
        if attempts > 10:
            break
    return num

# Get the data in original form for fitting- duplicate values and all.
def get_original_data(data):
    def expand_data_into_list(args):
        index = args[0]
        data = args[1]
        try:
            print("Processing building size", index)
            countframe = data[data["BuildingSize"] == index] # grab the row for that building size
            count = int(countframe["Count"].iloc[0]) # how many of the building
            listnum = [int(index)] # the building size
            expanded = listnum * count # Expand to a list of the size with len(count)
            expanded = pd.Series(expanded)
            return expanded
        except Exception as error:
            print("No index:", index)
            print(error)

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
    dist = scipy.stats.halfcauchy
    fit = scipy.stats.goodness_of_fit(dist, actual_data)
    print(fit)

def actual_data_to_hist(data):
    print("Binning...")
    # TODO: Isn't data technically already binned? value_counts() -> hist?
    # ANSWER: yes, but grouping larger bins improves the fit by raising them further from 0.
    # Fit to center points of bins? You could use resample() on that section to lump them together
    bin_interval = 100 # Large buildings bin size
    split_point = 201 # Where to switch to larger bins
    min_size = 2
    small_bins = list(range(min_size, split_point)) # Bin each small building size into its own bin
    large_bins = list(range(split_point, data.max() + 1, bin_interval))
    bins = small_bins + large_bins
    data = data[data >= min_size]
    hist, bin_edges = np.histogram(data, bins=bins)
    print(hist, "\n", bin_edges)
    return hist, bin_edges

# https://stackoverflow.com/questions/37396264/pandas-equivalent-of-resample-for-integer-index
def counted_data_to_hist(data):
    data_to_bin = data[data.index >= 200]
    rest_of_data = data[data.index < 200]
    groupby_labels = (data_to_bin.index.to_series() / 100).astype(int)
    newindex = groupby_labels.groupby(groupby_labels).apply(lambda x: np.mean(x.index))
    data_to_bin = data_to_bin.groupby(groupby_labels).median().set_index(newindex)
    return pd.concat([rest_of_data, data_to_bin])

def fit_data(data, dist):
    # Fit data to a distribution
    from typing import Optional
    def multivar_func(x, loc, scale):
        from math import exp, pi
        from scipy.special import factorial
        dist = "halfcauchy"
        match dist:
            case "halfcauchy":
                return (2/(pi * scale)) * (1/(1 + (x - loc)**2 / scale**2))
                # loc: 0.01407878, scale: 2.32293437
            case "poisson":
                # x is k, scale is mu
                x = x - loc
                return exp(0-scale) * ((scale**x) / factorial(x))
                # mu=1.12827518, loc=-0.0345403
            case _:
                return None
    
    # TODO: Look into kernel density estimation?
    # TODO: Extend rv_discrete with custom function to inherit rng methods

    print("Fitting...")
    data["Count"] = data["Count"].apply(int)
    data["Count"] = data["Count"] / data["Count"].sum()
    x = data.index.astype(int).values
    y = data["Count"]
    from numpy import inf
    parameters, covariance = scipy.optimize.curve_fit(dist.get_equation, x, y, bounds=(0, inf))
    print("Parameters:", parameters)
    print("Covariance:", covariance)

def test_visually(data, simulated_curve_count, sample_per_curve, dist, args):
    # Test fit of data visually
    # Fill missing sizes
    indices = pd.unique(data.index)
    max = int(indices[-1] + 1)
    index = range(0, max)
    data = data.reset_index()
    index = pd.Index(index, name="BuildingSize")
    data = data.set_index(["BuildingSize"]).reindex(index)

    # Get initial frame
    #numcounts = pd.Series(get_nums_wrapper(dist, sample_per_curve, args)).apply(decimal.Decimal)
    countFrame = data
    countFrame = countFrame.fillna(0)
    countFrame = countFrame.rename(columns={"Count": "Actual"})
    countFrame["Actual"] = countFrame["Actual"].apply(decimal.Decimal)
    countFrame["Actual"] = countFrame["Actual"] / countFrame["Actual"].sum() # Resize to proportion of data w/that size
    print("Sum of actual:", countFrame["Actual"].sum())

    # More copies to see range
    for i in range(1, simulated_curve_count + 1):
        numcounts = pd.Series(get_nums_wrapper(dist, sample_per_curve, args)).apply(decimal.Decimal)
        countFrame["Simulated " + str(i)] = numcounts
        print("Simulated curve", i, "done.")
    countFrame.sort_index(inplace=True)
    countFrame = countFrame.fillna(0)
    print(countFrame)
    #print("Actual count:", data["Count"].sum()) # For sampling reference
    # Graph it
    fig = px.line(countFrame, labels={
        "value": "Percentage of buildings with size", 
        "BuildingSize": "Unit Count"})
    max_x_axis_width = 50
    #fig.update_xaxes(autorangeoptions=dict(maxallowed=max_x_axis_width))
    fig.update_traces(opacity=0.75)
    fig.data[0].line.color = "#A9A9A9"
    fig.show()


def main():

    # Create custom distribution
    from scipy.stats import rv_discrete
    from math import pi, sqrt, e
    from numpy import log
    # Custom halfcauchy
    # loc: 0.14739042, scale: 2.34947676
    dist_loc1 = 1.74710558e-11
    dist_scale1 = 2.25850421e-01
    dist_loc1 = 0.14739042
    dist_scale1 = 2.34947676
    dist_loc2 = 5.24691790
    dist_scale2 = 2.80952836
    ACTION = "graph"
    simulated_curve_count = 3 # 30
    sample_per_curve = 1000
    large_building_bin_size = 100
    class building_dist(rv_discrete):
        def _argcheck(self, loc1, scale1):
            return True # Figure this out later, just need it to work for now
        # Currently returns 0s and nothing else.
        def _pmf(self, x, loc1, scale1):
            # Divide and log of denom of second part is 0
            return (2/(pi * scale1)) * (1/(1 + (x - loc1)**2 / scale1**2)) #+ \
            #return ((1/(x * scale2 * (sqrt(2 * pi)))) * e**((-1/2 * ((log(x) - loc2)) / scale2)**2))
        def get_equation(self, x, loc1, scale1, loc2, scale2):
            return (2/(pi * scale1)) * (1/(1 + (x - loc1)**2 / scale1**2)) + \
            ((1/(x * scale2 * (sqrt(2 * pi)))) * e**((-1/2 * ((log(x) - loc2)) / scale2)**2))

    dist = building_dist(name="building_dist")
    # Parameters for curve
    # halfcauchy
    #dist_loc = 2
    #dist_scale = 2.1624533028540704
    # Custom halfcauchy
    # loc: 0.14739042, scale: 2.34947676

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
    hud_counts["Count"] = hud_counts["Count"].apply(decimal.Decimal)
    #print("HUD counts:", hud_counts)
    # For now; add the nrel in future for better sample
    data = neea_data

    # Total count from census annual estimates of housing units for US in 2022
    # PROBLEM: scale is too big for fitting!

    buildings_in_us = 143789637
    buildings_in_sample = data["Count"].sum()
    # We need more precision than floats; hence, decimal module
    size_weight = decimal.Decimal(buildings_in_us / buildings_in_sample)
    # Scale up to approximate actual proportions, round to whole number because half units don't make sense
    data["Count"] = data["Count"] * size_weight
    #data["Count"] = data["Count"].astype(str)
    data["Count"] = data["Count"].apply(decimal.Decimal)
    data["Count"] = data["Count"].apply(decimal.Decimal.quantize, args=[decimal.Decimal("1.")])
    data = data.fillna(0)
    # Concat outliers into frame- done after weight because these buildings are very rare
    data = data.add(hud_counts, fill_value=0)
    data = data[data.index >= 2]

    # Rebin data to give larger buildings a shot at being fitted
    data = counted_data_to_hist(data)

    # Convert to percent of results at that size
    #data["Count"] = data["Count"] / data["Count"].sum()
    #print("Count sums to:", data["Count"].sum())
    match ACTION:
        case "fit":
            fit_data(data, dist)
        case "graph":
            #args = [dist_loc1, dist_scale1]
            args = [dist_loc1, dist_loc2, dist_scale1, dist_scale2]
            test_visually(data, simulated_curve_count, sample_per_curve, dist, args)
        case "goodness":
            goodness_fit_test(data)
        case "show":
            print(data)
        case "fitter-lib":
            fit_with_fitter(data)
        case "check_hist":
            print(data.index)


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