# Quick Setup

Work in progress; in the future, a single script will be documented here that can be run to fully set up the API and backend databases for use.

# Requirements

Python (3.12.2)
See requirements.txt for packages in use for this repository.
For API-specific packages, see /api/requirements.txt.

# Structure

The following directories are not guaranteed to be self-contained and may need refactoring after recent reorganization of this repository.

- DCT_testing holds files related to experimenting with DCT and privacy protection.
- building_aggregation holds files that create or export virtual buildings composed of multiple meters.
- building_analysis holds files that read from aggregated buildings (including, if necessary, decrypting them)

The following directories should be self-contained.
- api holds files related to running the API.
- deprecated holds code that isn't currently in use, but reflects past work.


# Further Documentation
For API-specific documentation, see /api/README.md.