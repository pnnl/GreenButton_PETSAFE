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

RETRIEVE_DCT = False

# Print the dataframe of coefficients

SHOW_DCT = False

# Graph the distribution of DCT coefficients

ANALYZE_DCT = False

# Graph the distribution of DCT coefficients per building

ANALYZE_DCT_PER_BUILDING = False