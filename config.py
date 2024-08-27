# ----- GENERAL -----

# Actions to perform
PREP_FILES = False
CREATE_BUILDINGS = True
CREATE_STATISTICS = False

# Database file target
DATABASE = "records.db"

# Set to true if you want to encrypt data before saving to file
ENCRYPT = False
# Set to True if processing encrypted data
DECRYPT = False
# Set to True if you'd prefer to save as pickle files, False for csv
SAVE_AS_PICKLE = True
# Fraction of CPU power to dedicate to processing, at most.
# If you have 4 cores and set this to 0.5, then 2 cores will be used.
PORTION_OF_CPU = 0.5

# ----- TEMPORAL RESOLUTION -----

# What resolution to retrieve statistics at
# "f": 15 minutes
# "h": hour
# "d": day
# "w": week
# "m": month
# "y": year
# 2024-08-05: implemented only for averages
# 2024-08-14: implemented for graphing
STAT_TEMPORAL_RESOLUTION = "f"

# What resolution to save buildings to file at
# "f": 15 minutes
# "h": hour
# "d": day
AGG_TEMPORAL_RESOLUTION = "f"

# What date range to retrieve statistics for
START_DATE = "2022-01-01"
END_DATE = "2022-01-01"

# ----- PROCESSING -----

# Which year of data to process. Should match a year in the data directory
YEAR = "2047"

# Size of buildings if buildings are being made at uniform size
BUILDING_SIZE = 8

# How many buildings to make per day if processing via distribution. 
# # Set to -1 for "as many as possible without duplicating sites"
# If processing multiple years for analysis, it's recommended to keep this value the same between years
BUILDING_COUNT = 1

# Output directory for prepped data
OUTPUT_DIR = "./output/"

# Where to log actions and issues
LOG_FILE = OUTPUT_DIR + 'building_processing.log'

# Root directory for input data
ROOT_DATA_DIR = "./data/" + YEAR + "-Full_v8.1/" + YEAR + "/"
ROOT_DATA_DIR = "./data"
# Name of target directory in root dir
POWER_DIR = ROOT_DATA_DIR + "power/"

# ----- ENCRYPTION AND RANDOMIZATION -----

# Which columns to encrypt
ENCRYPT_COLS = ["power", "apparent_power", "pf", "sites"]
# Seed to use for building site randomization
SEED = 176575734