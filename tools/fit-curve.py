from fitter import Fitter
import scipy
from pandas import read_csv

with open("./building-size-distribution.csv", "r") as file:
    data = read_csv(file)
"""
fitter = Fitter(data, timeout=60)
# TODO: exponential fails instantly. It might be a good fit- why?
fitter.distributions = ["exponential", "loglaplace", "burr12", "ncf", "halfgennorm", "alpha"]
fitter.fit()
summary = fitter.summary()
print("-------")
print(summary)
print(fitter.get_best())
"""

print("Exponential fit:")
loc, scale = scipy.stats.expon.fit(data)
print("loc:", loc)
print("scale:", scale)

#dist = scipy.stats.expon()
#exponfit = scipy.stats.fit(dist, data)
#print(exponfit)

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

"""
 Generate random numbers:
    >>> r = expon.rvs(size=1000)

rv = expon()
    >>> ax.plot(x, rv.pdf(x), 'k-', lw=2, label='frozen pdf')

ax.plot(x, expon.pdf(x),
    ...        'r-', lw=5, alpha=0.6, label='expon pdf')
"""