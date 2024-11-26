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
    building_id = 1
    power_sum_building_1 = reader.get_building_power_sum(building_id)
    power_avg_building_1 = reader.get_building_power_avg(building_id)

---

# Module Arguments

## MeterDataParser
- `file (str)`: a path to a file to process. Required.
- `seed (int)`: a seed to initialize prng. Optional, default randomly chosen.
- `building_size (int > 3)`: the number of sites to aggregate into a building. Optional, default `8`. Ignored if `distribution` is provided.
- `distribution`: A probability distribution for building sizes. Optional, default None.
- `key_location (str)`: the directory to store encryption keys in. Optional, default `"./keys/"`
- `algorithm (str)`: the algorithm to use for encryption. Any additively homomorphic algorithm offered by LightPHE may be provided. Optional, default `"EllipticCurve-ElGamal"`.
- `key_length (int)`: the length in bits of encryption keys. Optional, default `521`. This value should be changed to match recommendations for the chosen algorithm.
- `decimal_places (int > 0)`: the number of decimal places to keep for encrypted data; many encryption algorithms do not work with floats, so this value is used to convert to integers without undesired loss of precision. Optional, default is `5`.
- `encrypt (boolean)`: whether to encrypt data homomorphically. Default `True`.

## Reader
- `start_date (str)`: the start date of the period to read data for. Should be formatted as `"YYYY-MM-DD"`, eg. `"2023-12-01"`.
- `end_date (str)`: the end date of the period to read data for. Optional, default is `None`. If not provided, the entire year listed in `start_date` will be read.

## Decryptor
- `key_location (str)`: the directory to read encryption keys from. Optional, default `"./keys/"`
- `algorithm (str)`: the algorithm to use for decryption. Any additively homomorphic algorithm offered by LightPHE may be provided. Should match the value given to MeterDataParser when processing the data. Optional, default `"EllipticCurve-ElGamal"`.
- `decimal_places (int > 0)`: the number of decimal places to keep for encrypted data; many encryption algorithms do not work with floats, so this value is used to convert from integers back to floats. Should match the value given to MeterDataParser when processing the data. Optional, default is `5`.

---

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