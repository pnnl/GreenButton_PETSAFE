# Quick Setup

An Ubuntu environment is generally expected by setup scripts. In particular, these scripts were developed on Xubuntu Noble Numbat (24.04.1 LTS), kernel version 6.8.0-71-generic.

Virtual building creation scripts were made to work with the EULR HEMS dataset, which can be found here:
https://neea.org/resources/the-northwest-end-use-load-research-eulr-project

Virtual buildings can be created and exported to JSON via ``create_buildings.sh``. It's recommended that you review ``setup/exports_imports/building_aggregation/config.py`` before running this script to ensure that any building aggregation settings are appropriate for your goals. (This script depends on several other scripts in ``setup/exports_imports/building_aggregation``, so ensure that directory is present before running the script.)

``setup.sh`` can be run to set up the backend. This script installs dependencies (Python and assorted libraries, Influx and MySQL databases) if necessary, then fills the databases with sample data. The scripts run by this file can also be run individually if a specific part of setup is desired:

- If running on Ubuntu, you may run /setup/install-mysql.sh to do most of the setup for the MySQL database for you. (No guarantees it works yet- still testing)

If you'd like to test the API without setting up the backend, see API Integration Testing below.

## API Integration Testing

The API can be run in test mode and will return hardcoded JSON that matches the expected return as closely as possible (though formats are subject to change). Test mode does not require any additional setup, and it can be run without any databases or other backend. A script is provided to make running this test API as simple as possible (``test_api.sh``).

# Requirements

Python (3.12.3)
See requirements.txt for packages in use for this repository.


## API / Backend Requirements

MySQL (8.0.42-0ubuntu0.24.04.1)
InfluxDB (v2 and v3. V3 used for faster imports but could be replaced; otherwise not compatible yet)

# Structure

- api holds files related to running the API.
- output holds any files created as output by other scripts
- sample_energy_data holds JSON files. These files contain sample building energy usage records at a 15 minute time resolution.
- setup holds files related to setting up the backend, including scripts for creating sample buildings, SQL files, and scripts for setting up databases.

## Within /api
- dct_backend holds files used to test DCT on building data. It is not currently in use.
- docs contains documentation (TODO: needs updating).
- mockData contains JSON files used for the test API.
- scripts contains Python scripts used in the API (classes, repeated functions, etc.)
- sql will be removed in the future as soon as it's certain it's no longer in use

## Within /setup
- exports-and-imports contains files used to create, export, and import sample building energy records.
- sql contains SQL files used to set up the backend databases.


# Further Documentation
For API-specific documentation, see /api/README.md.