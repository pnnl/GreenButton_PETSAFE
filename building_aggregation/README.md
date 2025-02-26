PETSAFE (Privacy Enhancing Testbed for Secure meter Aggregation and Energy benchmarking)

# Contents
- [Quick Start](#quick-start)
- [Module Arguments](#module-arguments)
- [Packages](#required-packages)

# Quick Start
Edit config.py to configure settings for your use-case.
If using DCT, edit dct/dct_config.py for DCT-specific settings.

# Create database from energy data files
In main.py:
    populate_database()

## List files
    from list_files.py import *
    files = list_files_in_dir([directory path: str], [whether to append path to resulting files: bool])

## Process files in list into buildings
    import create_buildings as cb
    import config
    buildings = cb.make_buildings(config.BUILDING_COUNT, pickle=[bool], seed=config.SEED, encrypt=[bool])

To enable the use of homomorphic encryption, set `ENCRYPT` to `True` in config.py.

To set the number of buildings generated, set `BUILDING_COUNT` in config.py.

To set the temporal resolution for building aggregation, set `AGG_TEMPORAL_RESOLUTION` in config.py to one of the following values:
- `"f"`: every fifteen minutes
- `"h"`: hourly
- `"d"`: daily

To set the number of sites per building, set `MIN_SIZE` and `MAX_SIZE` in config.py. Site number will be selected within this range according to a model of real-world building sizes. To select a specific size, set `MIN_SIZE` and `MAX_SIZE` to the same value.
Larger building sizes will require more processing time and memory.

To set the date range, change `START_DATE` and `END_DATE` in config.py. Their values should be strings in the format `"YYYY-MM-DD"`, eg. `"2020-12-01"`. Smaller ranges will process more quickly.

## Decrypt files
    # Assuming that enc_building is a Building object with encryption True:
    # Get necessary components for decrypting a building
    cc = enc_building.get_cc()
    keys = enc_building.get_keys()
    order = enc_building.get_meter_order()
    length = enc_building.get_length()
    enc_data = enc_building.get_data()

    # Select a value to decrypt; in this case, the sum of all real power data at the first timestamp
    timestamp = enc_data.index[0]
    enc_power_sum = enc_data["real_power"].loc[enc_data.index == timestamp].iloc[0] # encrypted sum
    decryptor = Decryptor(keys=keys, cc=cc, order=order, length=length)
    dec_power_sum = decryptor.decrypt_target(enc_power_sum)

## Calculate sum and average of real power for a building
    Needs to be updated for new mechanisms; TODO

---

# Module Arguments

TODO

---

# Required packages
    lightphe
    pandas
    typing
    matplotlib
    math
    random
    os
    sys