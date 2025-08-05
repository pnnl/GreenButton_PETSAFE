# Frontend Testing

A test version of the API is available that does not require setup of the backend databases. To use the test version, run:

    python wgsi.py --test

from **within /api.** This version of the API returns hardcoded JSON that should (in the future) match the format of the data returned when querying against databases. 

At present, it returns hardcoded JSON that matches the JSON present in a frontend being developed for this backend; the format used there is different from the format currently in use for the backend, but the two will eventually match.

# Database Setup

## Automated setup

To automatically set up the databases, run /setup.sh

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

Consider using the sample data provided in /api/mockData for minimal effort in importing sample buildings.

To get JSON building data from scratch, see the main README.

## MySQL DB

Documentation for setting up MySQL and filling it with sample data can be found in the main README.