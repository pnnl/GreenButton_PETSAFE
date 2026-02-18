from pathlib import Path
csv_folder = 'interpolated-csv-files'
csv_path = Path(csv_folder)
files = [file for file in csv_path.iterdir() if file.is_file()]
print(files[0])

import os
# Force CPU usage to avoid CUDA warnings
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import warnings

def debug_data_issues(df):
    """Debug function to check data types and missing value representations"""
    power_col = 'real_power' if 'real_power' in df.columns else 'power'
    
    # print(f"DataFrame shape: {df.shape}")
    # print(f"DataFrame info:")
    # print(df.info())
    # print(f"\nPower column data type: {df[power_col].dtype}")
    
    # Check for different representations of missing values
    print(f"\nChecking different missing value representations:")
    print(f"pandas isnull(): {df[power_col].isnull().sum()}")
    print(f"pandas isna(): {df[power_col].isna().sum()}")
    
    # Check for string representations of NaN
    # if df[power_col].dtype == 'object':
    #     print(f"String 'NaN': {(df[power_col] == 'NaN').sum()}")
    #     print(f"String 'nan': {(df[power_col] == 'nan').sum()}")
    #     print(f"String 'NA': {(df[power_col] == 'NA').sum()}")
    #     print(f"String 'NULL': {(df[power_col] == 'NULL').sum()}")
    #     print(f"Empty strings: {(df[power_col] == '').sum()}")
    #     print(f"Whitespace only: {df[power_col].str.strip().eq('').sum()}")
    
    # Show unique values if there are few
    # unique_vals = df[power_col].unique()
    # if len(unique_vals) < 20:
    #     print(f"Unique values: {unique_vals}")
    # else:
    #     print(f"Number of unique values: {len(unique_vals)}")
    #     print(f"Sample values: {unique_vals[:10]}")
    
    # Check for specific problematic values
    print(f"\nChecking for problematic values:")
    if df[power_col].dtype == 'object':
        non_numeric = pd.to_numeric(df[power_col], errors='coerce').isnull()
        print(f"Values that can't be converted to numeric: {non_numeric.sum()}")
        if non_numeric.any():
            problematic = df.loc[non_numeric, power_col].unique()
            print(f"Problematic values: {problematic}")

def improved_find_gaps(df):
    """Improved gap finding with better debugging"""
    power_col = 'real_power' if 'real_power' in df.columns else 'power'
    
    # Convert to numeric first, marking non-numeric as NaN
    if df[power_col].dtype == 'object':
        print("Converting object column to numeric...")
        df[power_col] = pd.to_numeric(df[power_col], errors='coerce')
    
    is_nan = df[power_col].isnull()
    print(f"Total NaN values found: {is_nan.sum()}")
    
    if is_nan.sum() == 0:
        print("No gaps found!")
        return []
    
    # Show where NaN values are located
    nan_indices = df.index[is_nan].tolist()
    print(f"NaN indices: {nan_indices[:10]}..." if len(nan_indices) > 10 else f"NaN indices: {nan_indices}")
    
    # Find contiguous groups
    nan_diff = is_nan.diff()
    gap_starts = df.index[nan_diff & is_nan].tolist()
    gap_ends = df.index[nan_diff.shift(-1) & is_nan].tolist()
    
    # Handle edge cases
    if len(df) > 0 and is_nan.iloc[0]:
        gap_starts.insert(0, df.index[0])
    if len(df) > 0 and is_nan.iloc[-1]:
        gap_ends.append(df.index[-1])
    
    print(f"Gap starts: {gap_starts}")
    print(f"Gap ends: {gap_ends}")
    
    gaps = []
    for start, end in zip(gap_starts, gap_ends):
        try:
            start_idx = df.index.get_loc(start)
            end_idx = df.index.get_loc(end)
            gaps.append((start_idx, end_idx))
            print(f"Gap found: indices {start_idx} to {end_idx}")
        except KeyError as e:
            print(f"Error getting location for gap: {e}")
    
    return gaps


warnings.filterwarnings("ignore")

def find_gaps(df):
    """Find contiguous blocks of NaN values."""
    power_col = 'real_power' if 'real_power' in df.columns else 'power'
    is_nan = df[power_col].isnull()
    
    nan_diff = is_nan.diff()
    gap_starts = df.index[nan_diff & is_nan].tolist()
    gap_ends = df.index[nan_diff.shift(-1) & is_nan].tolist()
    
    if len(df) > 0 and is_nan.iloc[0]:
        gap_starts.insert(0, df.index[0])
    if len(df) > 0 and is_nan.iloc[-1]:
        gap_ends.append(df.index[-1])
    
    gaps = []
    for start, end in zip(gap_starts, gap_ends):
        start_idx = df.index.get_loc(start)
        end_idx = df.index.get_loc(end)
        gaps.append((start_idx, end_idx))
    
    return gaps

def create_sequences(data, look_back):
    """Create sequences for LSTM training."""
    if len(data) < look_back + 1:
        return np.array([]), np.array([])
    
    X, y = [], []
    for i in range(len(data) - look_back):
        X.append(data[i:(i + look_back)])
        y.append(data[i + look_back])
    return np.array(X), np.array(y)

def build_lstm_model(look_back):
    """Build LSTM model."""
    model = Sequential([
        LSTM(50, activation='relu', input_shape=(look_back, 1)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def train_and_predict_lstm_with_validation(training_data, gap_length, look_back=20):
    """Train LSTM and predict with validation checks."""
    print(f"    LSTM Details: {len(training_data)} training points, predicting {gap_length} values")
    
    if len(training_data) < look_back + 10:
        print(f"    -> Insufficient training data (need >{look_back + 10} points)")
        return None
    
    # Scale data
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(training_data.reshape(-1, 1))
    
    # Create sequences
    X, y = create_sequences(scaled_data.flatten(), look_back)
    
    if len(X) < 10:
        print(f"    -> Too few training sequences ({len(X)})")
        return None
    
    # Train model
    model = build_lstm_model(look_back)
    history = model.fit(X, y, epochs=50, batch_size=min(32, len(X)), verbose=0)
    
    final_loss = history.history['loss'][-1]
    print(f"    -> Training completed, final loss: {final_loss:.6f}")
    
    # Generate predictions
    predictions = []
    last_sequence = scaled_data[-look_back:].flatten()
    
    for i in range(gap_length):
        pred = model.predict(last_sequence.reshape(1, look_back, 1), verbose=0)
        predictions.append(pred[0, 0])
        last_sequence = np.append(last_sequence[1:], pred[0, 0])
    
    # Inverse transform
    predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
    
    print(f"    -> Predictions range: [{predictions.min():.2f}, {predictions.max():.2f}]")
    
    return predictions

def compare_imputation_results(original_df, imputed_df, context_points=5):
    """
    Compare original vs imputed data around each gap.
    """
    power_col = 'real_power' if 'real_power' in original_df.columns else 'power'
    
    # Find gaps in original data
    gaps = find_gaps(original_df)
    
    print("\n" + "="*80)
    print("IMPUTATION COMPARISON RESULTS")
    print("="*80)
    
    comparison_results = []
    
    for i, (start_idx, end_idx) in enumerate(gaps):
        gap_length = end_idx - start_idx + 1
        
        print(f"\n--- Gap {i+1}/{len(gaps)} ---")
        print(f"Location: indices {start_idx} to {end_idx}")
        print(f"Gap length: {gap_length} points")
        
        # Calculate context window
        context_start = max(0, start_idx - context_points)
        context_end = min(len(original_df), end_idx + 1 + context_points)
        
        # Extract data for comparison
        original_context = original_df.iloc[context_start:context_end].copy()
        imputed_context = imputed_df.iloc[context_start:context_end].copy()
        
        # Add position markers
        original_context['Position'] = ['Before'] * (start_idx - context_start) + \
                                     ['GAP'] * gap_length + \
                                     ['After'] * (context_end - end_idx - 1)
        
        imputed_context['Position'] = ['Before'] * (start_idx - context_start) + \
                                    ['IMPUTED'] * gap_length + \
                                    ['After'] * (context_end - end_idx - 1)
        
        # Create comparison DataFrame
        comparison = pd.DataFrame({
            'Index': range(context_start, context_end),
            'Original': original_context[power_col],
            'Imputed': imputed_context[power_col],
            'Position': original_context['Position'],
            'Difference': imputed_context[power_col] - original_context[power_col]
        })
        
        # Add timestamp if available
        if isinstance(original_df.index, pd.DatetimeIndex):
            comparison['Timestamp'] = original_context.index
        
        print("\nComparison (Original vs Imputed):")
        print("-" * 60)
        
        # Format the output nicely
        for idx, row in comparison.iterrows():
            position_marker = f"[{row['Position']:>7}]"
            if row['Position'] == 'GAP':
                original_val = "    NaN"
                imputed_val = f"{row['Imputed']:7.2f}"
                diff_val = "    ---"
            else:
                original_val = f"{row['Original']:7.2f}"
                imputed_val = f"{row['Imputed']:7.2f}"
                diff_val = f"{row['Difference']:7.2f}" if not pd.isna(row['Difference']) else "   0.00"
            
            timestamp_str = ""
            if 'Timestamp' in comparison.columns:
                timestamp_str = f" | {row['Timestamp']}"
            
            print(f"{position_marker} Orig: {original_val} | Imp: {imputed_val} | Diff: {diff_val}{timestamp_str}")
        
        # Calculate statistics for the imputed gap
        if gap_length > 1:
            gap_values = imputed_context[power_col].iloc[start_idx-context_start:end_idx-context_start+1]
            before_values = original_context[power_col].iloc[:start_idx-context_start].dropna()
            after_values = original_context[power_col].iloc[end_idx-context_start+1:].dropna()
            
            if len(before_values) > 0 and len(after_values) > 0:
                context_mean = pd.concat([before_values, after_values]).mean()
                context_std = pd.concat([before_values, after_values]).std()
                
                # print(f"\nGap Statistics:")
                # print(f"  Imputed values mean: {gap_values.mean():.2f}")
                # print(f"  Context mean: {context_mean:.2f}")
                # print(f"  Context std: {context_std:.2f}")
                # print(f"  Gap smoothness: {gap_values.std():.2f}")
        
        # Store for potential plotting
        comparison_results.append({
            'gap_number': i + 1,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'comparison_df': comparison
        })
    
    return comparison_results

def create_before_after_plots(original_df, imputed_df, plot_name="power_data", save_html=True, output_dir="./"):
    """
    Create two line plots: one before imputation (with gaps) and one after imputation.
    Plots timestamp_x vs real power.
    
    Parameters:
    original_df: DataFrame with gaps (NaN values)
    imputed_df: DataFrame with imputed values  
    plot_name: Name to use for the plot files and titles
    save_html: Whether to save plots as HTML files
    output_dir: Directory to save HTML files
    """
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import os
        
        power_col = 'real_power' if 'real_power' in original_df.columns else 'power'
        gaps = find_gaps(original_df)
        
        html_files = []
        
        # Use timestamp_x column as x-axis and real power as y-axis
        if isinstance(original_df.index, pd.DatetimeIndex):
            timestamp_col = original_df.index
        else:
            # Look for timestamp_x column specifically
            if 'timestamp_x' in original_df.columns:
                timestamp_col = pd.to_datetime(original_df['timestamp_x'])
            else:
                raise ValueError("No timestamp_x column found. DataFrame must have DatetimeIndex or 'timestamp_x' column.")
        
        # Plot 1: Before Imputation (with gaps)
        print(f"Creating 'Before Imputation' plot for {plot_name}...")
        
        # Create DataFrame for px.line - timestamp_x vs real power
        before_plot_df = pd.DataFrame({
            'Timestamp': timestamp_col,
            'Real_Power': original_df[power_col].values
        })
        
        # Create the line plot - timestamp_x vs real power
        fig_before = px.line(before_plot_df, x='Timestamp', y='Real_Power', 
                            title=f"{plot_name} - Before Imputation (Original Data with Gaps)",
                            labels={'Timestamp': 'Timestamp', 'Real_Power': 'Real Power'})
        
        # Update line style
        fig_before.update_traces(line=dict(color='blue', width=2))
        
        # Highlight gap regions
        if len(gaps) > 0:
            y_min = original_df[power_col].min() * 0.95
            y_max = original_df[power_col].max() * 1.05
            
            for i, (start_idx, end_idx) in enumerate(gaps):
                gap_start_x = timestamp_col.iloc[start_idx]
                gap_end_x = timestamp_col.iloc[end_idx]
                
                # Add shaded region for gap
                fig_before.add_shape(
                    type="rect",
                    x0=gap_start_x, y0=y_min,
                    x1=gap_end_x, y1=y_max,
                    fillcolor="red", opacity=0.2,
                    layer="below", line_width=0
                )
                
                # Add gap annotation
                gap_center_x = gap_start_x + (gap_end_x - gap_start_x) / 2
                fig_before.add_annotation(
                    x=gap_center_x,
                    y=y_max * 0.9,
                    text=f"Gap {i+1}<br>({end_idx-start_idx+1} pts)",
                    showarrow=False,
                    bgcolor="red",
                    opacity=0.8,
                    font=dict(color="white", size=10)
                )
        
        fig_before.update_layout(
            width=1200,
            height=600,
            hovermode='x unified',
            showlegend=False,
            xaxis_title="Timestamp",
            yaxis_title="Real Power"
        )
        
        # Save before plot
        if save_html:
            filename_before = f"{plot_name}_before_imputation.html"
            filepath_before = os.path.join(output_dir, filename_before)
            fig_before.write_html(filepath_before)
            html_files.append(filepath_before)
            print(f"  -> Saved 'Before' plot to: {filepath_before}")
        
        # Plot 2: After Imputation (complete data)
        print(f"Creating 'After Imputation' plot for {plot_name}...")
        
        # Create DataFrame for px.line - timestamp_x vs real power
        after_plot_df = pd.DataFrame({
            'Timestamp': timestamp_col,
            'Real_Power': imputed_df[power_col].values
        })
        
        # Create the line plot - timestamp_x vs real power
        fig_after = px.line(after_plot_df, x='Timestamp', y='Real_Power',
                           title=f"{plot_name} - After Imputation (Complete Data)",
                           labels={'Timestamp': 'Timestamp', 'Real_Power': 'Real Power'})
        
        # Update line style
        fig_after.update_traces(line=dict(color='green', width=2))
        
        # Highlight where gaps were filled
        if len(gaps) > 0:
            y_min = imputed_df[power_col].min() * 0.95
            y_max = imputed_df[power_col].max() * 1.05
            
            for i, (start_idx, end_idx) in enumerate(gaps):
                gap_start_x = timestamp_col.iloc[start_idx]
                gap_end_x = timestamp_col.iloc[end_idx]
                
                # Add shaded region where imputation occurred
                fig_after.add_shape(
                    type="rect",
                    x0=gap_start_x, y0=y_min,
                    x1=gap_end_x, y1=y_max,
                    fillcolor="yellow", opacity=0.3,
                    layer="below", line_width=1,
                    line_color="orange"
                )
                
                # Add imputation annotation
                gap_center_x = gap_start_x + (gap_end_x - gap_start_x) / 2
                fig_after.add_annotation(
                    x=gap_center_x,
                    y=y_max * 0.9,
                    text=f"Imputed {i+1}<br>({end_idx-start_idx+1} pts)",
                    showarrow=False,
                    bgcolor="orange",
                    opacity=0.8,
                    font=dict(color="white", size=10)
                )
        
        fig_after.update_layout(
            width=1200,
            height=600,
            hovermode='x unified',
            showlegend=False,
            xaxis_title="Timestamp",
            yaxis_title="Real Power"
        )
        
        # Save after plot
        if save_html:
            filename_after = f"{plot_name}_after_imputation.html"
            filepath_after = os.path.join(output_dir, filename_after)
            fig_after.write_html(filepath_after)
            html_files.append(filepath_after)
            print(f"  -> Saved 'After' plot to: {filepath_after}")
        
        return html_files
        
    except ImportError:
        print("Plotly not available. Install with: pip install plotly")
        return []
    
def impute_power_gaps(df, small_gap_threshold=4, training_window=100, 
                     show_comparison=True, create_plots=True, plot_name="power_data", 
                     save_html=True, output_dir="./"):
    """
    Main imputation function with before/after line plot visualization.
    Uses timestamp_x column for timestamps.
    """
    
    # Store original for comparison
    original_df = df.copy()
    
    df_processed = df.copy()
    
    # Set up timestamp_x as index if needed
    if 'timestamp_x' in df_processed.columns:
        df_processed['timestamp_x'] = pd.to_datetime(df_processed['timestamp_x'])
        if not isinstance(df_processed.index, pd.DatetimeIndex):
            df_processed.set_index('timestamp_x', inplace=True)
    
    # Determine power column
    if 'real_power' in df_processed.columns:
        power_col = 'real_power'
    elif 'power' in df_processed.columns:
        power_col = 'power'
    else:
        raise ValueError("DataFrame must have 'real_power' or 'power' column")
    
    print(f"Number of NaN values: {df_processed[power_col].isna().sum()}")
    
    gaps = find_gaps(df_processed)
    print(f"Found {len(gaps)} gaps to process.")
    
    # ... rest of the imputation logic remains the same ...
    
    # Store gap information for comparison
    processed_gaps = []
    
    for i, (start_idx, end_idx) in enumerate(gaps):
        gap_length = end_idx - start_idx + 1
        print(f"\nProcessing gap {i+1}/{len(gaps)}: indices {start_idx}-{end_idx} (length: {gap_length})")
        
        imputation_method = "linear"
        
        if gap_length <= small_gap_threshold:
            print("  -> Using linear interpolation (small gap)")
            
            if start_idx > 0 and end_idx < len(df_processed) - 1:
                before_val = df_processed[power_col].iloc[start_idx - 1]
                after_val = df_processed[power_col].iloc[end_idx + 1]
                interpolated_values = np.linspace(before_val, after_val, gap_length + 2)[1:-1]
                df_processed[power_col].iloc[start_idx:end_idx + 1] = interpolated_values
            else:
                # Edge case: forward fill or backward fill
                df_processed[power_col].fillna(method='ffill', inplace=True)
                df_processed[power_col].fillna(method='bfill', inplace=True)
        
        else:
            print("  -> Using LSTM imputation (large gap)")
            imputation_method = "LSTM"
            
            # Collect training data from before and after the gap
            training_data = []
            
            # Data before gap
            before_start = max(0, start_idx - training_window)
            before_data = df_processed[power_col].iloc[before_start:start_idx].dropna()
            if len(before_data) > 0:
                training_data.extend(before_data.values)
            
            # Data after gap
            after_end = min(len(df_processed), end_idx + 1 + training_window)
            after_data = df_processed[power_col].iloc[end_idx + 1:after_end].dropna()
            if len(after_data) > 0:
                training_data.extend(after_data.values)
            
            training_data = np.array(training_data)
            
            if len(training_data) >= 30:  # Minimum data requirement for LSTM
                predictions = train_and_predict_lstm_with_validation(training_data, gap_length)
                
                if predictions is not None:
                    df_processed[power_col].iloc[start_idx:end_idx + 1] = predictions
                    print(f"  -> Successfully imputed {gap_length} values using LSTM")
                else:
                    print("  -> LSTM failed, using linear interpolation as fallback")
                    imputation_method = "linear_fallback"
                    # Fallback to linear interpolation
                    if start_idx > 0 and end_idx < len(df_processed) - 1:
                        before_val = df_processed[power_col].iloc[start_idx - 1]
                        after_val = df_processed[power_col].iloc[end_idx + 1]
                        interpolated_values = np.linspace(before_val, after_val, gap_length + 2)[1:-1]
                        df_processed[power_col].iloc[start_idx:end_idx + 1] = interpolated_values
            else:
                print(f"  -> Insufficient training data ({len(training_data)} points), using linear interpolation")
                imputation_method = "linear_fallback"
                # Fallback to linear interpolation
                if start_idx > 0 and end_idx < len(df_processed) - 1:
                    before_val = df_processed[power_col].iloc[start_idx - 1]
                    after_val = df_processed[power_col].iloc[end_idx + 1]
                    interpolated_values = np.linspace(before_val, after_val, gap_length + 2)[1:-1]
                    df_processed[power_col].iloc[start_idx:end_idx + 1] = interpolated_values
        
        processed_gaps.append({
            'gap_number': i + 1,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'length': gap_length,
            'method': imputation_method
        })
    
    print(f"\nAfter imputation:")
    print(f"Number of remaining NaN values: {df_processed[power_col].isna().sum()}")
    
    # Show comparison if requested
    comparison_results = None
    if show_comparison and len(gaps) > 0:
        comparison_results = compare_imputation_results(original_df, df_processed)
    
    # Create before/after line plots
    html_files = []
    if create_plots:
        print(f"\nCreating before/after line plots...")
        html_files = create_before_after_plots(
            original_df, df_processed,
            plot_name=plot_name,
            save_html=save_html, 
            output_dir=output_dir
        )
        
        if html_files:
            print(f"\nHTML files created:")
            for file in html_files:
                print(f"  - {file}")
            print()
    
    return df_processed, processed_gaps, html_files

# **Other main block, I used this to check for the nan values.

# Replace your main execution with this:
# if __name__ == '__main__':
#     print("=== DEBUGGING DATA ISSUES ===\n")
    
#     # Load first file for debugging
#     first_file = files[90]
#     print(f"Debugging file: {first_file}")
#     for file in files:
#         df_debug = pd.read_csv(file, usecols=['timestamp_x', 'real_power'])
        
#         # Debug the data
#         debug_data_issues(df_debug)
        
#         print("\n" + "="*60)
#         print("TESTING GAP DETECTION")
#         print("="*60)
        
#         # Test gap detection
#         gaps = improved_find_gaps(df_debug.copy())
#         print(f"Found {len(gaps)} gaps")
        
#         # If gaps are found, let's examine them closely
#         # if gaps:
#         #     for i, (start_idx, end_idx) in enumerate(gaps):
#         #         print(f"\nExamining gap {i+1}:")
#         #         print(f"Indices: {start_idx} to {end_idx}")
                
#         #         # Show actual values around the gap
#         #         context_start = max(0, start_idx - 3)
#         #         context_end = min(len(df_debug), end_idx + 4)
                
#         #         context_data = df_debug.iloc[context_start:context_end].copy()
#         #         context_data['is_null'] = context_data['real_power'].isnull()
                
#         #         print("Context data:")
#         #         print(context_data)
    
#     # print("\n" + "="*60)
#     # print("MANUAL CHECK")
#     # print("="*60)
    
#     # Let's manually check some areas where gaps are supposedly found
#     # if gaps:
#     #     first_gap = gaps[0]
#     #     start_idx, end_idx = first_gap
        
#     #     print(f"Manual check of first gap (indices {start_idx}-{end_idx}):")
#     #     manual_check = df_debug.iloc[start_idx:end_idx+1]
#     #     print(manual_check['real_power'].values)
#     #     print(f"Are these actually NaN? {manual_check['real_power'].isnull().values}")


# Example usage and testing
if __name__ == '__main__':
    print("=== LSTM Power Data Imputation Tool - Before/After Line Plots ===\n")
    
    # Create sample data for demonstration
    # print("Creating sample dataset...")
    # date_rng = pd.date_range(start='2023-01-01', end='2023-01-05', freq='15min')
    # df_sample = pd.DataFrame({
    #     'timestamp': date_rng,
    #     'real_power': np.sin(np.arange(len(date_rng)) / 50) * 50 + 75 + np.random.normal(0, 2, len(date_rng))
    # })

    df_sample = pd.read_csv(files[0], usecols = ['timestamp_x', 'real_power'])
    
    # Introduce realistic gaps
    # print("Introducing gaps in the data...")
    # df_sample.loc[50:52, 'real_power'] = np.nan    # Small gap (3 points)
    # df_sample.loc[150:165, 'real_power'] = np.nan  # Medium gap (16 points)
    # df_sample.loc[250:280, 'real_power'] = np.nan  # Large gap (31 points)
    # df_sample.loc[350:352, 'real_power'] = np.nan  # Small gap (3 points)
    
    # print(f"Sample dataset created with {len(df_sample)} points")
    # print(f"Introduced {df_sample['real_power'].isna().sum()} missing values")
    
    # Run the imputation process with custom plot name
    print("\n" + "="*60)
    print("STARTING IMPUTATION PROCESS")
    print("="*60)
    
    for file in files:
        name = file.name.split('.')[0]
        df_sample = pd.read_csv(file, usecols = ['timestamp_x', 'real_power'])
        result_df, gap_info, html_files = impute_power_gaps(
            df_sample.copy(), 
            small_gap_threshold=4,           # Gaps <= 4 points use linear interpolation
            training_window=100,             # Use 100 points before/after for LSTM training
            show_comparison=False,            # Show detailed comparison
            create_plots=True,               # Create before/after line plots
            plot_name=name, # Custom name for the plots
            save_html=True,                  # Save plots as HTML files
            output_dir="./csv-plot-output"                  # Save in current directory
        )
    
    # Summary
    print("\n" + "="*60)
    print("IMPUTATION COMPLETE")
    print("="*60)
    
    print(f"\nGap Processing Summary:")
    for gap in gap_info:
        print(f"  Gap {gap['gap_number']}: Length {gap['length']} -> Method: {gap['method']}")
    
    if html_files:
        print(f"\nVisualization files created:")
        for file in html_files:
            print(f"  - {file}")
        print("\nTwo line plots created: Before and After imputation!")
        print("Open these HTML files in your browser to view the results!")
    
    print(f"\nFinal result: {result_df['real_power'].isna().sum()} remaining NaN values")
    print("Imputation process completed successfully!")