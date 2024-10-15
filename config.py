# ----- GENERAL -----

# Actions to perform
# For DCT-related actions, see next section

# Read from CSV files into SQLite database
READ_FILES = False
# Create virtual buildings using database
CREATE_BUILDINGS = False
# Database file target
DATABASE = "records.db"
# Set to true if you want to encrypt data before saving to file
ENCRYPT = True
# Set to True if you'd prefer to save as pickle files
SAVE_AS_PICKLE = True
# Fraction of CPU power to dedicate to processing, at most.
# e.g. If you have 4 cores and set this to 0.5, then 2 cores will be used.
PORTION_OF_CPU = 0.5

# Process statistics from created buildings
CREATE_STATISTICS = False
# Set to True if processing encrypted data
DECRYPT = False

# ----- DCT PROCESSING -----
# Use DCT to "smooth out" data, obscuring some transitional events
# Enables all other DCT processing switches
PERFORM_DCT = False
# Get DCT values for each day, then graph them.
DAILY_DCT_GRAPH = True
# Aggregate data to temporal resolution specified by STAT_TEMPORAL_RESOLUTION
# before performing DCT
AGGREGATE_BEFORE_DCT = False
# Perform DCT for one day instead of on the entire time period
DCT_ONE_DAY = False
# Test different methods of reducing DCT coefficients
FIT_DCT = False
# Method used for fitting. Options:
# "threshold"
# "drop high"
# "drop high keep max"
METHOD = "threshold"
# Normalize data to be between 0 and 1 before calculating DCT
NORMALIZE = True
# Graph the original data against the DCT-processed data before saving it
GRAPH_DCT = False
# Save DCT coefficients to pickle files
STORE_DCT = True
# Only save/load high-frequency DCT coefficients
HIGH_ONLY = False
# Cutoff point for considering something "high frequency"; e.g.
# 0.25 treats the top 25% of coefficients as being "high frequency"
# Must be between 0 and 1
HIGH_THRESHOLD = 0.75

# ----- DCT OPERATIONS -----
# Retrieve saved DCT values for analysis or further use
# Enables all other post-processing/operations switches
RETRIEVE_DCT = True
# Print the dataframe of coefficients
SHOW_DCT = False
# Graph the distribution of DCT coefficients
ANALYZE_DCT = False
# Graph the distribution of DCT coefficients per building
ANALYZE_DCT_PER_BUILDING = False


# ----- TEMPORAL RESOLUTION -----

# What resolution to retrieve statistics at
# "f": 15 minutes
# "h": hour
# "d": day
# "w": week
# "m": month
# "y": year
# Not yet re-implemented in full; use with caution
STAT_TEMPORAL_RESOLUTION = "d"

# What date range to retrieve statistics for
LIMIT_DATE = True
START_DATE = "2021-01-01"
END_DATE = "2021-12-31"


# ----- PROCESSING -----
# How many virtual buildings to make
BUILDING_COUNT = 30
# What building ID number to start at
FIRST_BUILDING_ID = 0
# Minimum and maximum count of units per building
MIN_SIZE = 2
MAX_SIZE = 5

# Output directory for prepped data
OUTPUT_DIR = "./output/"

# Where to log actions and issues
LOG_FILE = OUTPUT_DIR + 'building_processing.log'

# Root directory for input data
ROOT_DATA_DIR = "./data"
# Name of target directory in root dir
POWER_DIR = ROOT_DATA_DIR + "power/"


# ----- ENCRYPTION AND RANDOMIZATION -----

# Which columns to encrypt
# ["real_power", "apparent_power", "pf"]
ENCRYPT_COLS = ["real_power"]
# Seed to use for building site randomization
SEED = 176575734