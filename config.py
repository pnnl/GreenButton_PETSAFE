# ----- GENERAL -----

# Actions to perform
PREP_FILES = False
CREATE_STATISTICS = True

# Set to true if you want to encrypt data before saving to file
ENCRYPT = False
# Set to True if processing encrypted data
DECRYPT = False
# Set to True if you'd prefer to save as pickle files, False for csv
SAVE_AS_PICKLE = True

# ----- TEMPORAL RESOLUTION -----

# What resolution to retrieve statistics at
# "f": 15 minutes
# "h": hour
# "d": day
# "w": week
# "m": month
# "y": year
# 2024-08-05: implemented only for averages
STAT_TEMPORAL_RESOLUTION = "f"

# What resolution to save buildings to file at
# "f": 15 minutes
# "h": hour
# "d": day
AGG_TEMPORAL_RESOLUTION = "f"

# What date range to retrieve statistics for
START_DATE = "2023-07-05"
END_DATE = "2023-08-30"

# ----- FILE TARGETS FOR PROCESSING -----

# Which year of data to process. Should match a year in the data directory
YEAR = "2023"

# Output directory for prepped data
OUTPUT_DIR = "./output/"

# Root directory for input data
ROOT_DATA_DIR = "./data/" + YEAR + "-Full_v8.1/" + YEAR + "/"
# Name of target directory in root dir
POWER_DIR = ROOT_DATA_DIR + "power/"

# ----- ENCRYPTION AND RANDOMIZATION -----

# Which columns to decrypt
DECRYPT = ["power", "apparent_power", "pf"]
# Seed to use for building site randomization
SEED = 482249327