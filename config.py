# ----- GENERAL -----

# Actions to perform
# For DCT-related actions, see next section

# Read from CSV files into SQLite database
READ_FILES = False
# Create virtual buildings using database
CREATE_BUILDINGS = True
# Database file target
DATABASE = "data/records.db"
# Set to true if you want to encrypt data before saving to file
ENCRYPT = True
# Sets number of readings per encryption vector
BATCH_SIZE = 2
# Set to True if you'd prefer to save as pickle files
SAVE_AS_PICKLE = True
# Fraction of CPU power to dedicate to processing, at most.
# e.g. If you have 4 cores and set this to 0.5, then 2 cores will be used.
PORTION_OF_CPU = 0.5

# Process statistics from created buildings
CREATE_STATISTICS = False
# Set to True if processing encrypted data
DECRYPT = False

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
START_DATE = "2023-04-01"
END_DATE = "2023-04-02"


# ----- PROCESSING -----
# How many virtual buildings to make
BUILDING_COUNT = 1
# What building ID number to start at
FIRST_BUILDING_ID = 0
# Minimum and maximum count of units per building
MIN_SIZE = 2
MAX_SIZE = 2

# Output directory for prepped data
OUTPUT_DIR = "./output/"

# Where to log actions and issues
LOG_FILE = OUTPUT_DIR + 'building_processing.log'

# Root directory for input data
ROOT_DATA_DIR = "./data"
# Name of target directory in root dir
POWER_DIR = ROOT_DATA_DIR + "power/"

# Enables all other DCT processing switches
PERFORM_DCT = False

# ----- ENCRYPTION AND RANDOMIZATION -----

# Which columns to encrypt
# ["real_power", "apparent_power", "pf"]
ENCRYPT_COLS = ["real_power"]
# Seed to use for building site randomization
SEED = 176575734