from fitter import Fitter
import scipy
from math import floor
import plotly.express as px
import numpy
from pandas import read_csv

with open("./building-size-distribution.csv", "r") as file:
    data = read_csv(file)
data = data.set_index(["BuildingSize"])

"""
seed = numpy.random.randint(100000000, 999999999)
dist_loc = 1
dist_scale = 2.8406122167267887
dist_c = 0.3923899300763164
dist = scipy.stats.expon
known_params = {"c": dist_c, "loc": dist_loc, "scale": dist_scale}
# (dist_c, loc=dist_loc, scale=dist_scale)
#fit = scipy.stats.goodness_of_fit(dist, data["Count"], known_params=known_params)
#fit = scipy.stats.goodness_of_fit(dist, data["Count"])
#print(fit)
"""
import pandas as pd

# Get the data in original form for fitting- duplicate values and all.
actual_data = pd.Series()
indices = pd.unique(data.index)
data = data.reset_index()
for index in indices:
    try:
        countframe = data[data["BuildingSize"] == index]
        count = countframe["Count"].iloc[0]
        listnum = [int(index)]
        expanded = listnum * count
        expanded = pd.Series(expanded)
        actual_data = pd.concat([actual_data, expanded])
    except Exception as error:
        print("No index:", index)
        print(error)

# Using fitter library to find best fit with params
fitter = Fitter(actual_data, timeout=30)
#fitter.distributions = ["exponential", "loglaplace", "burr12", "ncf", "halfgennorm", "recipinvgauss", "alpha"]
fitter.fit()
summary = fitter.summary()
print("-------")
print(summary)
print(fitter.get_best())
# Results:
#             sumsquare_error          aic          bic  kl_div  ks_statistic     ks_pvalue
# lomax             0.000146  1644.025381  1655.521029     inf      0.155425  1.165421e-07
# genpareto         0.000146  1644.025778  1655.521426     inf      0.155425  1.165421e-07
# pareto            0.000146  1644.027669  1655.523316     inf      0.155425  1.165421e-07
# levy              0.000148  1650.078976  1657.742741     inf      0.144518  1.116687e-06
# nct               0.000150  1647.454892  1662.782422     inf      0.124782  4.363519e-05
# Recommended params for best fit:
# {'lomax': {'c': 0.5335113173075132, 'loc': 1.999999999569653, 'scale': 2.16217857286271}}

"""

# Test fit of data visually
import plotly.express as px
import pandas as pd
import math

# lomax
dist_loc = 1.999999999569653
dist_scale = 2.16217857286271
dist_c = 0.5335113173075132

def get_nums():
    nums = []
    for i in range(0, 341):
        num = 0
        while num < 2 or num > 480:
            #num = floor(scipy.stats.loglaplace.rvs(dist_c, loc=dist_loc, scale=dist_scale, size=1))
            #num = floor(scipy.stats.alpha.rvs(dist_a, loc=dist_loc, scale=dist_scale, size=1))
            #num = int(floor(scipy.stats.expon.rvs(loc=dist_loc, scale=dist_scale, size=1)))
            num = int(floor(scipy.stats.lomax.rvs(dist_c, loc=dist_loc, scale=dist_scale, size=1)))
        nums.append(num)
    print(nums)
    return nums


# Get initial frame
numseries = pd.Series(get_nums())
countSeries = numseries.value_counts(dropna=False)
countSeries = countSeries.fillna(0)
countFrame = data
countFrame["0"] = countSeries

# More copies to see range
for i in range(1,1):
    numseries = pd.Series(get_nums())
    countFrame[str(i)] = numseries
    # Compare against actual
#countFrame["actual"] = actual_data
countFrame.sort_index(inplace=True)
print("Actual count:", data["Count"].sum()) # For sampling reference
#print(countFrame)
# Graph it
bin_width= 2
#nbins = math.ceil((countFrame["count"].max() - countFrame["count"].min()) / bin_width)
fig = px.bar(countFrame)
fig.update_layout(barmode='group')
fig.update_traces(opacity=0.75)
fig.show()

 Generate random numbers:
    >>> r = expon.rvs(size=1000)

rv = expon()
    >>> ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')

ax.plot(x, expon.pdf(x),
    ...        'r-', lw=5, alpha=0.6, label='expon pdf')
"""