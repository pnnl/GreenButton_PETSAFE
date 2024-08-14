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
fitter = Fitter(data, timeout=60)
# TODO: exponential fails instantly. It might be a good fit- why?
# Alpha is great fit in sumsquare, not so much on other metrics.
# {'alpha': {'a': 3.395468413172602e-08, 'loc': 0.0008169558296610755, 'scale': 1.7034041729353762}}
fitter.distributions = ["exponential", "loglaplace", "burr12", "ncf", "halfgennorm", "recipinvgauss", "alpha"]
fitter.fit()
summary = fitter.summary()
print("-------")
print(summary)
print(fitter.get_best())

print("Exponential fit:")
loc, scale = scipy.stats.expon.fit(data)
print("loc:", loc)
print("scale:", scale)
"""

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
# Using fitter library instead
fitter = Fitter(actual_data, timeout=30)
#fitter.distributions = ["exponential", "loglaplace", "burr12", "ncf", "halfgennorm", "recipinvgauss", "alpha"]
fitter.fit()
summary = fitter.summary()
print("-------")
print(summary)
print(fitter.get_best())
# Suggests lowmax: {'lomax': {'c': 0.5335113173075132, 'loc': 1.999999999569653, 'scale': 2.16217857286271}}

"""
# Test fit of data visually
import plotly.express as px
import pandas as pd
import math

dist_loc = 0.9999999999999999
dist_scale = 2.8406122167267887
dist_c = 0.3923899300763164

def get_nums():
    nums = []
    for i in range(0, 341):
        num = 0
        while num < 2 or num > 480:
            #num = floor(scipy.stats.loglaplace.rvs(dist_c, loc=dist_loc, scale=dist_scale, size=1))
            #num = floor(scipy.stats.alpha.rvs(dist_a, loc=dist_loc, scale=dist_scale, size=1))
            num = int(floor(scipy.stats.expon.rvs(loc=dist_loc, scale=dist_scale, size=1)))
        nums.append(num)
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
countFrame["actual"] = data["Count"]
countFrame.sort_index(inplace=True)
print("Actual count:", data["Count"].sum()) # For sampling reference
print(countFrame)
# Graph it
bin_width= 2
#nbins = math.ceil((countFrame["count"].max() - countFrame["count"].min()) / bin_width)
fig = px.bar(countFrame)
fig.update_layout(barmode='group')
fig.update_traces(opacity=0.75)
fig.show()
"""

# Promising:
# Distribution  sumsquare_error    aic          bic             kl_div      ks_statistic    ks_pvalue
# alpha         0.000329           2020.178582  2030.248341     inf         0.371846        8.135829e-27
# loglaplace    0.000757           1691.233285  1701.303044     inf         0.316038        2.532737e-19
# burr12        0.000943           1658.304865  1671.731210     inf         0.299309        2.446751e-17
# ncf           0.001475           1646.532360  1663.315291     inf         0.193550        1.972215e-07
# halfgennorm   0.001778           1810.145085  1820.214844     inf         0.316038        2.532607e-19

# loglaplace params:
# {'loglaplace': {'c': 0.3923899300763164, 'loc': 0.9999999999999999, 'scale': 2.8406122167267887}}

# Exponential params:
# Exponential fit:
# loc: 1.0
# scale: 51.551886792452834
# Separately, with goodness of fit: loc=1.0, scale=2.2169811320754715
# And separately again: loc=1.000 scale=2.217
# Also separately: 52.69840754201713 14.097465343710727 0.3087576385840719

"""
 Generate random numbers:
    >>> r = expon.rvs(size=1000)

rv = expon()
    >>> ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')

ax.plot(x, expon.pdf(x),
    ...        'r-', lw=5, alpha=0.6, label='expon pdf')
"""