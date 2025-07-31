# ----- POPULATE RAW METER DATABASE -----
# Read from CSV files into SQLite database
READ_FILES = False
# Root directory for input data- where to find the dataset
ROOT_DATA_DIR = "./data"
# Name of target directory in root dir
POWER_DIR = ROOT_DATA_DIR + "power/"

# ----- AGGREGATE BUILDINGS -----
# Create virtual buildings using database
CREATE_BUILDINGS = False
# Location of database to read records from when creating buildings
# Expects a SQLite database
DATABASE = "/mnt/hgfs/records.db"
# Output directory for aggregated buildings
OUTPUT_DIR = "/home/petsafe/Desktop/PETSAFE/output/"
# Set to True if you'd prefer to save as pickle files
# (False defaults to CSV format on export)
SAVE_AS_PICKLE = True
# How many virtual buildings to make
BUILDING_COUNT = 20
# What building ID number to start at
# Increments by 1 per every new building
FIRST_BUILDING_ID = 0
# Minimum and maximum count of units per building
MIN_SIZE = 2
MAX_SIZE = 5
# Percentage of existing records necessary to accept an id as valid
# for building creation; e.g. 0.9 means the meter must have values for
# a minimum of 90% of its records within the specified time period
REQUIRED_PORTION = 0.9

# ----- ENCRYPT DURING AGGREGATION -----
# Set to true if you want to encrypt data before saving to file
ENCRYPT = False
# Sets number of expected readings per encryption vector
BATCH_SIZE = 96
# Which columns to encrypt
# Warning: more columns = more processing time
ENCRYPT_COLS = ["real_power", "apparent_power", "pf"]
# Seed to use for building site randomization
SEED = 1765757348

# ----- TEMPORAL RESOLUTION AND SCOPE -----

# What resolution to retrieve data at
# "f": 15 minutes
# "h": hour
# "d": day
# "w": week
# "m": month
# "y": year
# !!! Not yet re-implemented in full; change with caution !!!
# "f" should reliably work.
# Otherwise mostly used if encryption is enabled at present
STAT_TEMPORAL_RESOLUTION = "f"

# Whether to select data between set dates
# If false, retrieve all data- may take a long time!
LIMIT_DATE = True
# What date range to retrieve statistics for
# Inclusive values
START_DATE = "2023-01-01"
END_DATE = "2023-12-31"