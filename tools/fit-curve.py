from fitter import Fitter
import scipy
from math import floor
import plotly.express as px
import numpy
from pandas import read_csv

with open("./building-size-distribution.csv", "r") as file:
    data = read_csv(file)
data.set_index(["BuildingSize"])
"""
fitter = Fitter(data, timeout=60)
# TODO: exponential fails instantly. It might be a good fit- why?
# Alpha is great fit in sumsquare, not so much on other metrics. Excluded.
fitter.distributions = ["exponential", "loglaplace", "burr12", "ncf", "halfgennorm", "recipinvgauss"]
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

from fitter import HistFit
from matplotlib import pyplot
import scipy.stats
#Y, X, _ = hist(data, bins=107)

hf = HistFit(X=data.index, Y=data["Count"])
hf.fit(error_rate=0.03, Nfit=20)
print(hf.fitted_param['expon'])
print(hf.mu, hf.sigma, hf.amplitude)
"""

# Test fit of data visually
import plotly.express as px
import pandas as pd
import math
nums = []
dist_loc = 1
dist_scale = 2.8406122167267887
dist_c = 0.3923899300763164
dist = scipy.stats.expon
for i in range(0, 341):
    num = 0
    while num < 2 or num > 323:
        num = floor(scipy.stats.loglaplace.rvs(dist_c, loc=dist_loc, scale=dist_scale, size=1))
    nums.append(num)

numseries = pd.Series(nums)
countSeries = numseries.value_counts(dropna=False)
countSeries = countSeries.fillna(0)
countFrame = pd.DataFrame(data=countSeries)
countFrame["actual"] = data["Count"]
print("Actual count:", data["Count"].sum())
print(countFrame)

bin_width= 1
nbins = math.ceil((countFrame["count"].max() - countFrame["count"].min()) / bin_width)

fig = px.histogram(countFrame, nbins=nbins)

fig.update_layout(barmode='overlay')
fig.update_traces(opacity=0.75)
fig.show()


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
# Also separately: 52.69840754201713 14.097465343710727 0.3087576385840719

"""
 Generate random numbers:
    >>> r = expon.rvs(size=1000)

rv = expon()
    >>> ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')

ax.plot(x, expon.pdf(x),
    ...        'r-', lw=5, alpha=0.6, label='expon pdf')
"""