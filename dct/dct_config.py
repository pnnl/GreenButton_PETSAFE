# ----- BUILDING SOURCE -----

BUILDING_DIRECTORY = "data/buildings/"

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
# Sample week, no weekends: 2023-07-03 to 2023-07-08
LIMIT_DATE = True
START_DATE = "2023-07-03"
END_DATE = "2023-07-08"

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
HIGH_THRESHOLD = 0.5

# Test different methods of reducing DCT coefficients
DROP_COEFFICIENTS = False
# Method used for dropping coefficients. Options:
# "threshold"
# "drop high"
# "drop high keep max"
DROP_METHOD = "drop high"

# If using drop high keep max: how many largest coefficients to keep
NUMBER_OF_LARGEST = 5

# If using threshold: at what value and below to drop coefficients to 0
DROP_THRESHOLD = 10

# When graphing against actual demand curves, this determines how
# many actual days to select as comparison points.
# Make sure this value is smaller than the sample size.
COMPARISON_DATE_SAMPLE_SIZE = 5

# Whether to print additional debug information to console
PRINT_DEBUG = False

# ----- DCT OPERATIONS -----

# Graph a curve created by averaging DCT coefficients
# against actual demand curves to test visual similarity
MAKE_DCT_AVG_CURVE = True

# IF MAKE_DCT_AVG_CURVE is true:
# Apply differential privacy measures to the average curve
DCT_AVG_DP = True

# Retrieve saved DCT values for analysis or further use
# Enables all other post-processing/operations switches
RETRIEVE_DCT = False

# Print the dataframe of coefficients
SHOW_DCT = False

# ----- GRAPHING ---------

# Enable/disable all graphing switches
GRAPH_DCT = False
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
DCT_TARGET = "d"

# Graph the distribution of all DCT coefficients
GRAPH_OVERALL_COEFFICIENT_DIST = False
# Graph coefficients per day for a year of data; ~96 points per line, ~365 lines,
# one graph per building
GRAPH_BY_DAY = False
# Graph the distribution of DCT coefficients per building
GRAPH_COEFFICIENTS_PER_BUILDING = False