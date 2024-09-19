import pandas as pd
from sklearn.preprocessing import minmax_scale

# data should be a pandas frame column (series)
def normalize(data):
    data = data.to_numpy()
    return minmax_scale(data)

""" 
Logic:

Get list of all days in the database
for each day, normalize
get building (either very small for speed or size of whole dataset)
calculate DCT, add to file (pickle it)

Plot distribution of DCT coefficient sizes
(so you probably want this in PANDAS or a np array)

Measure efficacy of methods using time-weighted mean:
avg / sample count

it might be worthwhile to have a normalized version of the database file
normalization will probably come in handy again
"""