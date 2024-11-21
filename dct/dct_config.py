# ----- BUILDING SOURCE -----

BUILDING_DIRECTORY = "data/dct-buildings/"

# ----- DCT PROCESSING -----

# Use DCT to "smooth out" data, obscuring some transitional events
# Enables all other DCT processing switches
PERFORM_DCT = True

# Perform DCT for one day instead of on the entire time period
DCT_ONE_DAY = False

# Save DCT coefficients to pickle files
STORE_DCT = False

# ----- MODIFIERS -----

# Date limiters
LIMIT_DATE = True
START_DATE = "2023-01-01"
END_DATE = "2023-12-31"

# Normalize data to be between 0 and 1 before calculating DCT
NORMALIZE = True

# Resample data to temporal resolution specified by config.STAT_TEMPORAL_RESOLUTION
# before performing DCT
RESAMPLE_BEFORE_DCT = False

# Only save/load high-frequency DCT coefficients
HIGH_ONLY = False
# Cutoff point for considering something "high frequency"; e.g.
# 0.25 treats the top 25% of coefficients as being "high frequency"
# Must be between 0 and 1
HIGH_THRESHOLD = 0.75

# Test different methods of reducing DCT coefficients
DROP_COEFFICIENTS = False
# Method used for dropping coefficients. Options:
# "threshold"
# "drop high"
# "drop high keep max"
DROP_METHOD = "threshold"

# ----- DCT OPERATIONS -----

# Retrieve saved DCT values for analysis or further use
# Enables all other post-processing/operations switches
RETRIEVE_DCT = False

# Print the dataframe of coefficients
SHOW_DCT = False

# ----- GRAPHING ---------

# Enable/disable all graphing switches
GRAPH_DCT = True
# Graph coefficients as scatterplots
GRAPH_AS_SCATTER = False
# Graph coefficients as histograms
GRAPH_AS_HIST = False
# Graph coefficients as box plot
GRAPH_AS_BOX = False
# Graph original data against data recomposed from DCT coefficients
GRAPH_DATA_AGAINST_RECOMPOSED = False

# Size of the period to do DCT on
# Options:
# "d": once per day
# "y": once per year
# "a": on all available data for period
GRAPH_TARGET = "d"

# Graph the distribution of all DCT coefficients
GRAPH_OVERALL_COEFFICIENT_DIST = False
# Graph coefficients per day for a year of data; ~96 points per line, ~365 lines,
# one graph per building
GRAPH_BY_DAY = True
# Graph the distribution of DCT coefficients per building
GRAPH_COEFFICIENTS_PER_BUILDING = False