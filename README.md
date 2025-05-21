# Quick Setup

Work in progress; in the future, a single script will be documented here that can be run to fully set up the API and backend databases for use.

## API Integration Testing

The API can be run in test mode and will return hardcoded JSON that matches the expected return as closely as possible (though formats are subject to change). Test mode does not require any additional setup, and it can be run without any databases or other backend. A script is provided to make running this test API as simple as possible (test_api.sh).

# Requirements

Python (3.12.2)
See requirements.txt for packages in use for this repository.

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