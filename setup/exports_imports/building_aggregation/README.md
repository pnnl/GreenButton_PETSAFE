Warning: this documentation may be out of date.

# Contents
- [Quick Start](#quick-start)
- [Module Arguments](#module-arguments)
- [Packages](#required-packages)

# Quick Start
Edit config.py to configure settings for your use-case.
If using DCT, edit dct/dct_config.py for DCT-specific settings.

# Create SQLite database from energy data files

See pullMains.py in the processor module.

# Process SQLite metering data into buildings

The simplest way to create virtual buildings is to run create_buildings.py directly. Settings for building creation can be found in setup/exports_imports/building_aggregation/config.py; these settings should be checked before creating buildings.

To enable the use of homomorphic encryption, set `ENCRYPT` to `True` in config.py (see warning in "Decrypt files" section below first).

To set the number of buildings generated, set `BUILDING_COUNT` in config.py.

To set the temporal resolution for building aggregation, set `AGG_TEMPORAL_RESOLUTION` in config.py to one of the following values:
- `"f"`: every fifteen minutes
- `"h"`: hourly
- `"d"`: daily

At present, only a setting of "f" functions for unencrypted data. Other resolutions can be obtained by further aggregating the resulting buildings' data.

To set the number of sites per building, set `MIN_SIZE` and `MAX_SIZE` in config.py. The number of units aggregated into the building will be selected within this range according to a model of real-world building sizes. To select a specific size, set `MIN_SIZE` and `MAX_SIZE` to the same value.
Larger building sizes will require more processing time and memory.
If using the building creation script in the root directory, additional options for selecting building sizes will be presented.

To set the date range of the data used for aggregation, change `START_DATE` and `END_DATE` in config.py. Their values should be strings in the format `"YYYY-MM-DD"`, eg. `"2020-12-01"`. Smaller ranges will process more quickly; for testing purposes, a range of one month, one season, or one year may be more desirable than a wider range.

## Decrypt files

Warning: this code has not been used since the end of 2024 and thus may not behave as expected due to changes in the codebase since that time. Use with caution and test the success of encryption and decryption before relying on it.

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

As buildings can be exported as Pandas DataFrame objects, the use of .sum() and similar methods allows calculation of these statistics if performed on the real_power column.


# Aggregated Building Frame Output

| num | Column name               | Datatype            |
|-----|---------------------------|---------------------|
| 0   | building_id               | Int                 |
| 1   | point_id (list of sites)  | Str "(tuple of int)"|
| 2   | timestamp (index)         | Datetime            |
| 3   | duration                  | Int                 |
| 4   | real_power                | float               |
| 5   | apparent_power            | float               |
| 6   | PF                        | float               |
| 7   | quality                   | Int                 |
| 8   | raw_data_present          | Bool                |

``raw_data_present`` denotes whether the row's readings existed in the original data set. A value of False on a row where real_power has a value communicates that the row's value was imputed.

## Quality Encodings

0: "valid" (data is present and usable without notable issues),
8: "estimated_reference_day" (imputed using reference day from prior data),
9: "estimated_interpolation" (imputed using interpolation),
10: "questionable" (problems with original data mean this reading may not be 100% reliable or valid),
11: "derived",
13: "mixed",
14: "raw",
15: "other" (does not fit prior categories; may denote data that was not properly processed, as it was used as a default for all rows before assigning more relevant categories)
