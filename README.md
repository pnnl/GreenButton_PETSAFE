# Quick Setup

An Ubuntu environment is generally expected by setup scripts. In particular, these scripts were developed on Xubuntu Noble Numbat (24.04.1 LTS), kernel version 6.8.0-71-generic.

Virtual building creation scripts were made to work with the EULR HEMS dataset, which can be found here:
https://neea.org/resources/the-northwest-end-use-load-research-eulr-project

Virtual buildings can be created and exported to JSON via ``create_buildings.sh``. It's recommended that you review ``setup/exports_imports/building_aggregation/config.py`` before running this script to ensure that any building aggregation settings are appropriate for your goals. (This script depends on several other scripts in ``setup/exports_imports/building_aggregation``, so ensure that directory is present before running the script.)

There is one prerequisite for the building aggregation script to run as intended. A SQLite database containing the EULR HEMS dataset must be prepared. Scripts for doing so can be found in ``setup/exports_imports/building_aggregation/processor/`` (see ``setup/exports_imports/building_aggregation/processor/documentation.md`` for details on expected table formats)

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

## LSTM-based Demand Imputation Tool (`clean_csv.py`)

### Overview
The demand imputation tool uses LSTM neural networks to fill missing values (gaps) in power consumption time-series data. It analyzes data characteristics around the gaps to select an appropriate imputation strategy for energy data, considering the range of variability in the areas near the gap (i.e., to match the underlying demand data features).
The algorithm is divided into two phases. During the first phase, the algorithm is trained using a sliding window technique, where records from the current window are used to predict the next window. Training windows are only deployed where continuous records exist to learn "typical behavior". During the second phase, actual imputation occurs, filling in the blanks according to the trained model (or using linear interpolation when only a few missing points exist).

### Input Requirements
- **CSV files** containing time-series power data with:
  - A timestamp column (`timestamp_x`) 
  - A power measurement column (`real_power` or `power`)
  - Missing values should be represented as NaN or null entries
- Output files should be placed in the `interpolated-csv-files/` directory by default


### How It Works
The tool employs a three-tier imputation strategy:

1. **Data Analysis**: Examines each gap's surrounding data to calculate:
   - Coefficient of Variation (CV) - relative variability
   - Spike ratio - percentage of outliers (>2σ from mean)
   - Spike clusters - groups of consecutive outliers
   - Volatility - average absolute change between points
   - Sudden changes - frequency of extreme fluctuations

2. **Model Selection** (automatic when `approach='auto'`):
   - **Linear Interpolation**: Used to fill small gaps (≤4 points)
   - **Residual Modeling**: Highly spiky AND volatile data (spike_ratio >10%, sudden_changes >30%)
   - **Ensemble LSTM**: Data with multiple spike clusters (>3), uses three parallel networks at different time scales (10, 20, 40 steps)
   - **Enhanced Single LSTM**: Smoother data or fallback, uses deep 128→96→64 unit network

3. **Model Caching**: Trained models are cached to avoid retraining on identical data patterns, improving processing speed.

### Usage
Run the script directly to process all CSV files in the input directory:

```bash
python clean_csv.py
```

**Output**:
- Imputed CSV files saved to `imputed-csv-files/`
- Before/after visualization plots  are saved to `csv-plot-output/` (HTML)
- Console output showing gap detection, method selection, and processing statistics

### Key Features
- **Reproducibility**: The LTSM training uses a fixed random seed (42), to ensure identical results across multiple runs
- **Spike-aware loss function**: Custom loss function to ensure LTSM weights remain predictable
- **Multi-scale temporal modeling**: Ensemble approach captures short, medium, and long-term patterns simultaneously
- **Auto scaling**: The LTSM is able to scale to different demand scales. 
- **Fallback mechanisms**: Automatically uses simpler methods when insufficient data is available

### Configuration Parameters
Key parameters in `impute_power_gaps()`:
- `small_gap_threshold=4`: Maximum gap size for linear interpolation
- `training_window=200`: Number of surrounding points used for training
- `lstm_approach='auto'`: Algorithm selection ('auto', 'ensemble', 'residual', 'enhanced_single')
- `show_comparison=True`: Display before/after comparison tables
- `create_plots=True`: Generate HTML visualization plots



## Within /setup
- exports-and-imports contains files used to create, export, and import sample building energy records.
- sql contains SQL files used to set up the backend databases.


# Further Documentation
For API-specific documentation, see /api/README.md.