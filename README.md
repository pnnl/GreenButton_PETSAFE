# Requirements

Python (3.12.2)
See requirements.txt for packages in use for this repository.

# API

API-related files can be found in the API folder. This directory should be self-contained, but relies on the existence of MySQL and Influx databases containing data about meters, energy usage, customers, etc.

# Database Setup

## Automated setup

To automatically set up the databases, run ./setup.sh

## Influx DB

To import JSON building data into Influx, please see /api/docs/Influx-Setup.docx

JSON is expected in the following format:

{
    "timestamp": int of Unix datetime, e.g. 1672531200000; the start time of a reading
    "meter_id": int, e.g. 1; the unique ID for the meter
    "real_power": float, e.g. 3.145; the real power measurement for this reading
    "apparent_power": float, e.g. 3.145; the apparent power measurement for this reading
    "pf": float, e.g. 0.123; the power factor for this reading
    "privacy": str, e.g. "low"; the privacy level of this reading
    "meter_type": str, e.g. "aggregate"; whether the meter is raw data, aggregated/virtual, etc.
}

Consider using the sample data provided in /api/import-to-database/raw for minimal effort in importing sample buildings.

To get JSON building data from scratch, see the files in building-aggregation; these files were made to work with the EULR HEMS dataset, which can be found here:
https://neea.org/resources/the-northwest-end-use-load-research-eulr-project

Please unpack and place this data in the /data directory. It can be read into a SQLLite database for further processing by /building_aggregation/create_buildings.py (if creating randomized aggregates) or /main.py (populate_database(), processing raw data).

## MySQL DB

Documentation for setting up MySQL and filling it with sample data is currently being worked on; this README will reference it as soon as it's in place.

If running on Ubuntu, you may run /setup/install-mysql.sh to do most of the setup for the MySQL database for you.


# Other

## Structure

The following directories are not guaranteed to be self-contained and may need refactoring after recent reorganization of this repository.

- DCT_testing holds files related to experimenting with DCT and privacy protection.
- building_aggregation holds files that create or export virtual buildings composed of multiple meters.
- building_analysis holds files that read from aggregated buildings (including, if necessary, decrypting them)