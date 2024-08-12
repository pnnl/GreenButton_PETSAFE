PETSAFE (Privacy Enhancing Testbed for Secure meter Aggregation and Energy benchmarking)

# Quick Start
Edit config.py to configure settings for your use-case.

## List files
    files = list_files_in_dir([directory path: str], [whether to append path to resulting files: bool])

## Process files in list into buildings
    from virtual_buildings import meterdata as md
    import config
    parser = md.MeterDataParser(file, seed=config.SEED, encrypt=config.ENCRYPT)

To enable the use of homomorphic encryption, set `ENCRYPT` to `True` in config.py.

To set the temporal resolution for building aggregation, set `AGG_TEMPORAL_RESOLUTION` in config.py to one of the following values:
- `"f"`: every fifteen minutes
- `"h"`: hourly
- `"d"`: daily

To set the number of sites per building, pass `building_size=val` to `MeterDataParser`, where `val` equals the site count per building.

## Read from processed files between two dates
To set the date range, change `START_DATE` and `END_DATE` in config.py. Their values should be strings in the format `"YYYY-MM-DD"`, eg. `"2020-12-01"`.

    from building_analysis.reader import Reader
    reader = Reader(config.START_DATE, config.END_DATE)
    data = reader.get_data()

## Decrypt files
    from building_analysis.decryptor import Decryptor
    decryptor = Decryptor()
    example_value = data["power"].iloc[0] # requires pandas import
    test_value = decryptor.decrypt_target(example_value)

## Calculate sum and average of real power for a building
    building_id = 1
    power_sum_building_1 = reader.get_building_power_sum(building_id)
    power_avg_building_1 = reader.get_building_power_avg(building_id)

## Graph building real power for time period to file
    reader.graph_building_power(building_id)

# Required packages
    lightphe
    pandas
    multiprocessing
    typing
    matplotlib
    math
    random
    os
    sys