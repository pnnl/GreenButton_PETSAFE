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
from sklearn.preprocessing import MinMaxScaler, StandardScaler, RobustScaler
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Input, Concatenate, Attention, MultiHeadAttention
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import backend as K
import tensorflow as tf
import warnings
import random
import hashlib
import joblib


# --- MODIFICATION 1: REPEATABILITY SETUP ---

def set_seeds(seed=42):
    """
    Sets random seeds for reproducibility across multiple libraries.
    """
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    # The following line is crucial for full determinism with TensorFlow.
    # It may impact performance but ensures identical results on the same hardware.
    tf.config.experimental.enable_op_determinism()
    print(f"Seeds set for reproducibility (seed={seed})")

# Set seeds at the start of the script for all subsequent operations
SEED = 42
set_seeds(SEED)

# --- MODIFICATION 2: CACHING SETUP ---

MODEL_CACHE_DIR = Path('model_cache')
MODEL_CACHE_DIR.mkdir(exist_ok=True)
print(f"Model cache directory is set to: {MODEL_CACHE_DIR.resolve()}")
##Imputed results
output_csv_dir = 'imputed-csv-files'
Path(output_csv_dir).mkdir(parents=True, exist_ok=True)

def debug_data_issues(df):
    """Debug function to check data types and missing value representations"""
    power_col = 'real_power' if 'real_power' in df.columns else 'power'
    
    print(f"\nChecking different missing value representations:")
    print(f"pandas isnull(): {df[power_col].isnull().sum()}")
    print(f"pandas isna(): {df[power_col].isna().sum()}")
    
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
    
    if df[power_col].dtype == 'object':
        print("Converting object column to numeric...")
        df[power_col] = pd.to_numeric(df[power_col], errors='coerce')
    
    is_nan = df[power_col].isnull()
    print(f"Total NaN values found: {is_nan.sum()}")
    
    if is_nan.sum() == 0:
        print("No gaps found!")
        return []
    
    nan_indices = df.index[is_nan].tolist()
    print(f"NaN indices: {nan_indices[:10]}..." if len(nan_indices) > 10 else f"NaN indices: {nan_indices}")
    
    nan_diff = is_nan.diff()
    gap_starts = df.index[nan_diff & is_nan].tolist()
    gap_ends = df.index[nan_diff.shift(-1) & is_nan].tolist()
    
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

def extract_spike_features(data, window_size=5):
    """Extract features that help identify and model spikes"""
    features = {}
    
    # Moving statistics
    features['rolling_mean'] = pd.Series(data).rolling(window=window_size, center=True).mean().fillna(method='bfill').fillna(method='ffill')
    features['rolling_std'] = pd.Series(data).rolling(window=window_size, center=True).std().fillna(0)
    features['rolling_max'] = pd.Series(data).rolling(window=window_size, center=True).max().fillna(method='bfill').fillna(method='ffill')
    features['rolling_min'] = pd.Series(data).rolling(window=window_size, center=True).min().fillna(method='bfill').fillna(method='ffill')
    
    # Spike indicators
    features['deviation_from_mean'] = data - features['rolling_mean']
    features['normalized_deviation'] = features['deviation_from_mean'] / (features['rolling_std'] + 1e-8)
    
    # Rate of change
    features['diff1'] = np.diff(data, n=1, prepend=data[0])
    features['diff2'] = np.diff(data, n=2, prepend=[data[0], data[1]])
    
    # Volatility measure
    features['volatility'] = pd.Series(features['diff1']).rolling(window=window_size).std().fillna(0)
    
    return features

def analyze_data_characteristics(data):
    """Enhanced data analysis to detect spike patterns"""
    variance = np.var(data)
    mean = np.mean(data)
    std = np.std(data)
    
    # Calculate coefficient of variation
    cv = std / mean if mean != 0 else float('inf')
    
    # Detect spikes (values beyond 2 standard deviations)
    spike_threshold = 2 * std
    spikes = np.abs(data - mean) > spike_threshold
    spike_ratio = np.sum(spikes) / len(data)
    
    # Detect consecutive spikes (spike clusters)
    spike_clusters = 0
    in_cluster = False
    for is_spike in spikes:
        if is_spike and not in_cluster:
            spike_clusters += 1
            in_cluster = True
        elif not is_spike:
            in_cluster = False
    
    # Calculate volatility (average absolute difference)
    volatility = np.mean(np.abs(np.diff(data)))
    
    # Detect sudden changes
    changes = np.abs(np.diff(data))
    sudden_change_threshold = np.percentile(changes, 90)
    sudden_changes = np.sum(changes > sudden_change_threshold) / len(changes)
    
    print(f"    Data analysis: CV={cv:.3f}, Spike ratio={spike_ratio:.3f}")
    print(f"    Volatility={volatility:.2f}, Sudden changes={sudden_changes:.3f}")
    print(f"    Spike clusters={spike_clusters}")
    
    return {
        'coefficient_of_variation': cv,
        'spike_ratio': spike_ratio,
        'spike_clusters': spike_clusters,
        'volatility': volatility,
        'sudden_changes': sudden_changes,
        'variance': variance,
        'is_highly_variable': cv > 0.5,
        'has_many_spikes': spike_ratio > 0.1,
        'is_very_volatile': sudden_changes > 0.3
    }

def create_multi_scale_sequences(data, short_window=10, medium_window=20, long_window=40):
    """Create sequences at multiple time scales for better pattern recognition"""
    sequences = {}
    
    # Short-term patterns (spikes, immediate changes)
    if len(data) >= short_window + 1:
        X_short, y_short = [], []
        for i in range(len(data) - short_window):
            X_short.append(data[i:(i + short_window)])
            y_short.append(data[i + short_window])
        sequences['short'] = (np.array(X_short), np.array(y_short))
    
    # Medium-term patterns
    if len(data) >= medium_window + 1:
        X_medium, y_medium = [], []
        for i in range(len(data) - medium_window):
            X_medium.append(data[i:(i + medium_window)])
            y_medium.append(data[i + medium_window])
        sequences['medium'] = (np.array(X_medium), np.array(y_medium))
    
    # Long-term patterns
    if len(data) >= long_window + 1:
        X_long, y_long = [], []
        for i in range(len(data) - long_window):
            X_long.append(data[i:(i + long_window)])
            y_long.append(data[i + long_window])
        sequences['long'] = (np.array(X_long), np.array(y_long))
    
    return sequences

def spike_aware_loss(y_true, y_pred):
    """Custom loss function that gives higher weight to spike predictions"""
    # Standard MSE
    mse = K.mean(K.square(y_pred - y_true))
    
    # Higher weight for extreme values (potential spikes)
    threshold = K.std(y_true) * 1.5
    spike_mask = K.cast(K.abs(y_true - K.mean(y_true)) > threshold, K.floatx())
    
    # Spike-weighted loss
    spike_loss = K.mean(spike_mask * K.square(y_pred - y_true) * 3.0)  # 3x weight for spikes
    
    # Combine losses
    return mse + spike_loss

def build_spike_aware_ensemble(short_window, medium_window, long_window, data_characteristics):
    """Build an ensemble of LSTM models optimized for spiky data"""
    
    # Input layers for different time scales
    input_short = Input(shape=(short_window, 1), name='short_input')
    input_medium = Input(shape=(medium_window, 1), name='medium_input')
    input_long = Input(shape=(long_window, 1), name='long_input')
    
    # Short-term model (for immediate spikes)
    lstm_short = LSTM(64, activation='tanh', return_sequences=False, name='lstm_short')(input_short)
    lstm_short = Dropout(0.3)(lstm_short)
    dense_short = Dense(32, activation='relu', name='dense_short')(lstm_short)
    output_short = Dense(1, name='output_short')(dense_short)
    
    # Medium-term model (for pattern recognition)
    lstm_medium = LSTM(96, activation='tanh', return_sequences=True, name='lstm_medium_1')(input_medium)
    lstm_medium = Dropout(0.3)(lstm_medium)
    lstm_medium = LSTM(48, activation='tanh', return_sequences=False, name='lstm_medium_2')(lstm_medium)
    lstm_medium = Dropout(0.2)(lstm_medium)
    dense_medium = Dense(32, activation='relu', name='dense_medium')(lstm_medium)
    output_medium = Dense(1, name='output_medium')(dense_medium)
    
    # Long-term model (for context and trends)
    lstm_long = LSTM(128, activation='tanh', return_sequences=True, name='lstm_long_1')(input_long)
    lstm_long = Dropout(0.4)(lstm_long)
    lstm_long = LSTM(64, activation='tanh', return_sequences=True, name='lstm_long_2')(lstm_long)
    lstm_long = Dropout(0.3)(lstm_long)
    lstm_long = LSTM(32, activation='tanh', return_sequences=False, name='lstm_long_3')(lstm_long)
    dense_long = Dense(16, activation='relu', name='dense_long')(lstm_long)
    output_long = Dense(1, name='output_long')(dense_long)
    
    # Ensemble combination with learned weights
    combined = Concatenate(name='combine_outputs')([output_short, output_medium, output_long])
    
    # Attention-like mechanism to weight different scales
    if data_characteristics['has_many_spikes']:
        # More weight on short-term for spiky data
        weights = Dense(3, activation='softmax', name='attention_weights')(combined)
        final_output = Dense(1, name='final_output')(combined)
    else:
        # Balanced weights for smoother data
        final_output = Dense(1, name='final_output')(combined)
    
    # Create the model
    model = Model(inputs=[input_short, input_medium, input_long], outputs=final_output)
    
    # Custom optimizer for volatile data
    optimizer = Adam(learning_rate=0.0005, clipnorm=1.0, beta_1=0.9, beta_2=0.999)
    
    # Use spike-aware loss for very spiky data
    if data_characteristics['has_many_spikes']:
        model.compile(optimizer=optimizer, loss=spike_aware_loss, metrics=['mae'])
    else:
        model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])
    
    return model

def residual_modeling_approach_old(training_data, gap_length, look_back=30):
    """Model the differences/residuals instead of absolute values for better spike handling"""
    print(f"    Using residual modeling approach...")
    
    # Calculate differences (first-order residuals)
    residuals = np.diff(training_data)
    
    # Fit a simple trend to the original data
    x = np.arange(len(training_data))
    trend_coeffs = np.polyfit(x, training_data, deg=1)
    trend = np.polyval(trend_coeffs, x)
    
    # Detrend the data
    detrended = training_data - trend
    
    # Create sequences for residual prediction
    if len(residuals) < look_back + 1:
        return None
    
    X_res, y_res = [], []
    for i in range(len(residuals) - look_back):
        X_res.append(residuals[i:(i + look_back)])
        y_res.append(residuals[i + look_back])
    
    X_res, y_res = np.array(X_res), np.array(y_res)
    
    if len(X_res) < 10:
        return None
    
    # Scale residuals
    scaler = RobustScaler()
    X_res_scaled = scaler.fit_transform(X_res.reshape(-1, 1)).reshape(X_res.shape)
    y_res_scaled = scaler.transform(y_res.reshape(-1, 1)).flatten()
    
    # Build residual prediction model
    model = Sequential([
        LSTM(64, activation='tanh', input_shape=(look_back, 1), return_sequences=True),
        Dropout(0.3),
        LSTM(32, activation='tanh', return_sequences=False),
        Dropout(0.2),
        Dense(16, activation='relu'),
        Dense(1)
    ])
    
    model.compile(optimizer=Adam(learning_rate=0.001), loss='huber', metrics=['mae'])
    
    # Train the model
    X_res_scaled = X_res_scaled.reshape(X_res_scaled.shape[0], X_res_scaled.shape[1], 1)
    model.fit(X_res_scaled, y_res_scaled, epochs=100, batch_size=16, verbose=0)
    
    # Generate predictions
    last_residuals = residuals[-look_back:]
    last_residuals_scaled = scaler.transform(last_residuals.reshape(-1, 1)).flatten()
    
    predicted_residuals = []
    current_sequence = last_residuals_scaled.copy()
    
    for i in range(gap_length):
        pred_res = model.predict(current_sequence.reshape(1, look_back, 1), verbose=0)[0, 0]
        predicted_residuals.append(pred_res)
        current_sequence = np.append(current_sequence[1:], pred_res)
    
    # Inverse transform residuals
    predicted_residuals = scaler.inverse_transform(np.array(predicted_residuals).reshape(-1, 1)).flatten()
    
    # Reconstruct absolute values
    last_value = training_data[-1]
    predicted_values = []
    
    # Extend trend
    trend_slope = trend_coeffs[0]
    start_idx = len(training_data)
    
    for i, res in enumerate(predicted_residuals):
        # Add trend component
        trend_component = trend_slope * (start_idx + i) + trend_coeffs[1]
        # Add predicted residual
        predicted_value = last_value + np.sum(predicted_residuals[:i+1])
        predicted_values.append(predicted_value)
    
    return np.array(predicted_values)

def train_and_predict_spike_aware_lstm_old(training_data, gap_length, approach='ensemble'):
    """Advanced LSTM training with multiple approaches for spiky data"""
    print(f"    Advanced LSTM Details: {len(training_data)} training points, predicting {gap_length} values")
    print(f"    Using approach: {approach}")
    
    min_data_points = max(60, gap_length * 4)  # Increased minimum
    if len(training_data) < min_data_points:
        print(f"    -> Insufficient training data (need >{min_data_points} points)")
        return None
    
    # Analyze data characteristics
    data_char = analyze_data_characteristics(training_data)
    
    # Choose approach based on data characteristics
    if approach == 'auto':
        if data_char['has_many_spikes'] and data_char['is_very_volatile']:
            approach = 'residual'
        elif data_char['spike_clusters'] > 3:
            approach = 'ensemble'
        else:
            approach = 'enhanced_single'
    
    print(f"    -> Selected approach: {approach}")
    
    if approach == 'residual':
        return residual_modeling_approach(training_data, gap_length)
    
    elif approach == 'ensemble':
        
        # Multi-scale ensemble approach
        short_window, medium_window, long_window = 10, 20, 40
        
        # Ensure we have enough data for all windows
        if len(training_data) < long_window + 20:
            print("    -> Not enough data for ensemble, using enhanced single model")
            approach = 'enhanced_single'
        else:
            sequences = create_multi_scale_sequences(training_data, short_window, medium_window, long_window)
            
            if len(sequences) < 3:
                print("    -> Cannot create all sequence scales, using enhanced single model")
                approach = 'enhanced_single'
            else:
                # Scale data
                scaler = RobustScaler()
                scaled_data = scaler.fit_transform(training_data.reshape(-1, 1)).flatten()
                
                # Create multi-scale sequences
                sequences_scaled = create_multi_scale_sequences(scaled_data, short_window, medium_window, long_window)
                
                # Build and train ensemble model
                model = build_spike_aware_ensemble(short_window, medium_window, long_window, data_char)
                
                # Prepare training data
                X_short = sequences_scaled['short'][0].reshape(-1, short_window, 1)
                X_medium = sequences_scaled['medium'][0].reshape(-1, medium_window, 1)
                X_long = sequences_scaled['long'][0].reshape(-1, long_window, 1)
                y_train = sequences_scaled['short'][1]  # Use short-term targets
                
                # Align data lengths
                min_len = min(len(X_short), len(X_medium), len(X_long))
                X_short = X_short[:min_len]
                X_medium = X_medium[:min_len]
                X_long = X_long[:min_len]
                y_train = y_train[:min_len]
                
                # Train model
                callbacks = [
                    EarlyStopping(monitor='loss', patience=20, restore_best_weights=True),
                    ReduceLROnPlateau(monitor='loss', factor=0.5, patience=10, min_lr=1e-6)
                ]
                
                model.fit(
                    [X_short, X_medium, X_long], y_train,
                    epochs=200,
                    batch_size=min(16, len(X_short) // 4),
                    callbacks=callbacks,
                    verbose=0
                )
                
                # Generate predictions
                predictions = []
                last_short = scaled_data[-short_window:]
                last_medium = scaled_data[-medium_window:]
                last_long = scaled_data[-long_window:]
                
                for i in range(gap_length):
                    pred = model.predict([
                        last_short.reshape(1, short_window, 1),
                        last_medium.reshape(1, medium_window, 1),
                        last_long.reshape(1, long_window, 1)
                    ], verbose=0)[0, 0]
                    
                    predictions.append(pred)
                    
                    # Update sequences
                    last_short = np.append(last_short[1:], pred)
                    last_medium = np.append(last_medium[1:], pred)
                    last_long = np.append(last_long[1:], pred)
                
                # Inverse transform
                predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
                
                return predictions
    
    # Enhanced single model approach (fallback or direct choice)
    if approach == 'enhanced_single':
        look_back = 35  # Increased lookback
        
        # Add feature engineering
        features = extract_spike_features(training_data)
        
        # Use robust scaling
        scaler = RobustScaler()
        scaled_data = scaler.fit_transform(training_data.reshape(-1, 1)).flatten()
        
        # Create sequences
        X, y = [], []
        for i in range(len(scaled_data) - look_back):
            X.append(scaled_data[i:(i + look_back)])
            y.append(scaled_data[i + look_back])
        
        X, y = np.array(X), np.array(y)
        
        if len(X) < 15:
            return None
        
        # Enhanced model architecture
        model = Sequential([
            LSTM(128, activation='tanh', input_shape=(look_back, 1), return_sequences=True),
            Dropout(0.4),
            LSTM(96, activation='tanh', return_sequences=True),
            Dropout(0.3),
            LSTM(64, activation='tanh', return_sequences=False),
            Dropout(0.2),
            Dense(32, activation='relu'),
            Dropout(0.1),
            Dense(16, activation='relu'),
            Dense(1)
        ])
        
        # Use Huber loss for robustness to outliers
        optimizer = Adam(learning_rate=0.0008, clipnorm=1.0)
        
        if data_char['has_many_spikes']:
            model.compile(optimizer=optimizer, loss=spike_aware_loss, metrics=['mae'])
        else:
            model.compile(optimizer=optimizer, loss='huber', metrics=['mae'])
        
        # Enhanced training
        callbacks = [
            EarlyStopping(monitor='loss', patience=25, restore_best_weights=True),
            ReduceLROnPlateau(monitor='loss', factor=0.7, patience=15, min_lr=1e-6)
        ]
        
        X = X.reshape(X.shape[0], X.shape[1], 1)
        
        model.fit(
            X, y,
            epochs=250,  # More epochs
            batch_size=min(12, len(X) // 5),  # Smaller batches
            callbacks=callbacks,
            verbose=0
        )
        
        # Generate predictions with noise injection for diversity
        predictions = []
        last_sequence = scaled_data[-look_back:]
        
        for i in range(gap_length):
            pred = model.predict(last_sequence.reshape(1, look_back, 1), verbose=0)[0, 0]
            
            # Add small random variation for spiky data to prevent flat lines
            if data_char['has_many_spikes'] and i > 0:
                noise_scale = np.std(scaled_data) * 0.05  # 5% noise
                pred += np.random.normal(0, noise_scale)
            
            predictions.append(pred)
            last_sequence = np.append(last_sequence[1:], pred)
        
        # Inverse transform
        predictions = scaler.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        
        # Post-processing: ensure realistic bounds
        data_min, data_max = np.min(training_data), np.max(training_data)
        data_range = data_max - data_min
        lower_bound = data_min - 0.3 * data_range
        upper_bound = data_max + 0.3 * data_range
        predictions = np.clip(predictions, lower_bound, upper_bound)
        
        print(f"    -> Final predictions range: [{predictions.min():.2f}, {predictions.max():.2f}]")
        
        return predictions
    
    return None

def residual_modeling_approach(training_data, gap_length, look_back=30):
    """Model the differences/residuals with integrated caching."""
    print(f"    Using residual modeling approach...")
    
    # --- Caching Logic ---
    data_hash = hashlib.sha256(training_data.tobytes()).hexdigest()
    cache_key = f"residual_{data_hash}_{gap_length}_{look_back}_{SEED}"
    model_path = MODEL_CACHE_DIR / f"{cache_key}_model.keras"
    scaler_path = MODEL_CACHE_DIR / f"{cache_key}_scaler.pkl"
    
    residuals = np.diff(training_data)
    
    if model_path.exists() and scaler_path.exists():
        print("    -> Loading 'residual' model and scaler from cache.")
        model = tf.keras.models.load_model(model_path)
        scaler = joblib.load(scaler_path)
    else:
        print("    -> Training new 'residual' model.")
        if len(residuals) < look_back + 1: return None
        
        X_res, y_res = [], []
        for i in range(len(residuals) - look_back):
            X_res.append(residuals[i:(i + look_back)])
            y_res.append(residuals[i + look_back])
        X_res, y_res = np.array(X_res), np.array(y_res)
        
        if len(X_res) < 10: return None
        
        scaler = RobustScaler()
        X_res_scaled = scaler.fit_transform(X_res.reshape(-1, 1)).reshape(X_res.shape)
        y_res_scaled = scaler.transform(y_res.reshape(-1, 1)).flatten()
        
        model = Sequential([
            LSTM(64, activation='tanh', input_shape=(look_back, 1), return_sequences=True),
            Dropout(0.3), LSTM(32, activation='tanh', return_sequences=False),
            Dropout(0.2), Dense(16, activation='relu'), Dense(1)
        ])
        model.compile(optimizer=Adam(learning_rate=0.001), loss='huber', metrics=['mae'])
        
        X_res_scaled = X_res_scaled.reshape(X_res_scaled.shape[0], X_res_scaled.shape[1], 1)
        model.fit(X_res_scaled, y_res_scaled, epochs=100, batch_size=16, verbose=0)

        print("    -> Caching new 'residual' model and scaler.")
        model.save(model_path)
        joblib.dump(scaler, scaler_path)

    # --- Prediction Logic (common for cached and new model) ---
    last_residuals = residuals[-look_back:]
    last_residuals_scaled = scaler.transform(last_residuals.reshape(-1, 1)).flatten()
    
    predicted_residuals_scaled = []
    current_sequence = last_residuals_scaled.copy()
    
    for _ in range(gap_length):
        pred_res = model.predict(current_sequence.reshape(1, look_back, 1), verbose=0)[0, 0]
        predicted_residuals_scaled.append(pred_res)
        current_sequence = np.append(current_sequence[1:], pred_res)
        
    predicted_residuals = scaler.inverse_transform(np.array(predicted_residuals_scaled).reshape(-1, 1)).flatten()
    
    last_value = training_data[-1]
    predicted_values = last_value + np.cumsum(predicted_residuals)
    
    return predicted_values

# [Rest of the code remains the same - compare_imputation_results, create_before_after_plots, etc.]
def train_and_predict_spike_aware_lstm(training_data, gap_length, approach='auto'):
    """Advanced LSTM training with multiple approaches, caching, and reproducibility."""
    print(f"    Advanced LSTM Details: {len(training_data)} training points, predicting {gap_length} values")
    
    min_data_points = max(60, gap_length * 4)
    if len(training_data) < min_data_points:
        print(f"    -> Insufficient training data (need >{min_data_points} points)")
        return None
        
    data_char = analyze_data_characteristics(training_data)
    
    final_approach = approach
    if approach == 'auto':
        if data_char['has_many_spikes'] and data_char['is_very_volatile']:
            final_approach = 'residual'
        elif data_char['spike_clusters'] > 3:
            final_approach = 'ensemble'
        else:
            final_approach = 'enhanced_single'
    print(f"    -> Selected approach: {final_approach}")
    
    if final_approach == 'residual':
        return residual_modeling_approach(training_data, gap_length)
    
    elif final_approach == 'ensemble':
        short_window, medium_window, long_window = 10, 20, 40
        if len(training_data) < long_window + 20:
            print("    -> Not enough data for ensemble, falling back to single model.")
            final_approach = 'enhanced_single'
        else:
            data_hash = hashlib.sha256(training_data.tobytes()).hexdigest()
            cache_key = f"ensemble_{data_hash}_{gap_length}_{SEED}"
            model_path = MODEL_CACHE_DIR / f"{cache_key}_model.keras"
            scaler_path = MODEL_CACHE_DIR / f"{cache_key}_scaler.pkl"

            if model_path.exists() and scaler_path.exists():
                print("    -> Loading 'ensemble' model and scaler from cache.")
                custom_objects = {'spike_aware_loss': spike_aware_loss} if data_char['has_many_spikes'] else {}
                model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
                scaler = joblib.load(scaler_path)
                scaled_data = scaler.transform(training_data.reshape(-1, 1)).flatten()
            else:
                print("    -> Training new 'ensemble' model.")
                scaler = RobustScaler()
                scaled_data = scaler.fit_transform(training_data.reshape(-1, 1)).flatten()
                
                sequences_scaled = create_multi_scale_sequences(scaled_data, short_window, medium_window, long_window)
                if len(sequences_scaled) < 3:
                    print("    -> Cannot create all sequence scales, falling back to single model.")
                    final_approach = 'enhanced_single'
                else:
                    model = build_spike_aware_ensemble(short_window, medium_window, long_window, data_char)
                    X_short = sequences_scaled['short'][0].reshape(-1, short_window, 1)
                    X_medium = sequences_scaled['medium'][0].reshape(-1, medium_window, 1)
                    X_long = sequences_scaled['long'][0].reshape(-1, long_window, 1)
                    y_train = sequences_scaled['short'][1]
                    
                    min_len = min(len(X_short), len(X_medium), len(X_long))
                    X_short, X_medium, X_long, y_train = X_short[:min_len], X_medium[:min_len], X_long[:min_len], y_train[:min_len]
                    
                    callbacks = [EarlyStopping(monitor='loss', patience=20, restore_best_weights=True), ReduceLROnPlateau(monitor='loss', factor=0.5, patience=10, min_lr=1e-6)]
                    
                    model.fit([X_short, X_medium, X_long], y_train, epochs=200, batch_size=min(16, len(X_short) // 4), callbacks=callbacks, verbose=0)
                    
                    print("    -> Caching new 'ensemble' model and scaler.")
                    model.save(model_path)
                    joblib.dump(scaler, scaler_path)

            if final_approach == 'ensemble': # Check again in case of fallback
                predictions_scaled = []
                current_short = scaled_data[-short_window:]
                current_medium = scaled_data[-medium_window:]
                current_long = scaled_data[-long_window:]
                
                for _ in range(gap_length):
                    pred = model.predict([current_short.reshape(1, short_window, 1), current_medium.reshape(1, medium_window, 1), current_long.reshape(1, long_window, 1)], verbose=0)[0, 0]
                    predictions_scaled.append(pred)
                    current_short = np.append(current_short[1:], pred)
                    current_medium = np.append(current_medium[1:], pred)
                    current_long = np.append(current_long[1:], pred)
                    
                return scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1)).flatten()

    if final_approach == 'enhanced_single':
        look_back = 35
        data_hash = hashlib.sha256(training_data.tobytes()).hexdigest()
        cache_key = f"single_{data_hash}_{gap_length}_{SEED}"
        model_path = MODEL_CACHE_DIR / f"{cache_key}_model.keras"
        scaler_path = MODEL_CACHE_DIR / f"{cache_key}_scaler.pkl"

        if model_path.exists() and scaler_path.exists():
            print("    -> Loading 'enhanced_single' model and scaler from cache.")
            custom_objects = {'spike_aware_loss': spike_aware_loss} if data_char['has_many_spikes'] else {}
            model = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
            scaler = joblib.load(scaler_path)
            scaled_data = scaler.transform(training_data.reshape(-1, 1)).flatten()
        else:
            print("    -> Training new 'enhanced_single' model.")
            scaler = RobustScaler()
            scaled_data = scaler.fit_transform(training_data.reshape(-1, 1)).flatten()
            
            X, y = [], []
            for i in range(len(scaled_data) - look_back):
                X.append(scaled_data[i:(i + look_back)])
                y.append(scaled_data[i + look_back])
            X, y = np.array(X), np.array(y)
            
            if len(X) < 15: return None
            
            model = Sequential([
                LSTM(128, activation='tanh', input_shape=(look_back, 1), return_sequences=True), Dropout(0.4),
                LSTM(96, activation='tanh', return_sequences=True), Dropout(0.3),
                LSTM(64, activation='tanh', return_sequences=False), Dropout(0.2),
                Dense(32, activation='relu'), Dropout(0.1),
                Dense(16, activation='relu'), Dense(1)
            ])
            
            optimizer = Adam(learning_rate=0.0008, clipnorm=1.0)
            loss_func = spike_aware_loss if data_char['has_many_spikes'] else 'huber'
            model.compile(optimizer=optimizer, loss=loss_func, metrics=['mae'])
            
            callbacks = [EarlyStopping(monitor='loss', patience=25, restore_best_weights=True), ReduceLROnPlateau(monitor='loss', factor=0.7, patience=15, min_lr=1e-6)]
            
            X = X.reshape(X.shape[0], X.shape[1], 1)
            model.fit(X, y, epochs=250, batch_size=min(12, len(X) // 5), callbacks=callbacks, verbose=0)
            
            print("    -> Caching new 'enhanced_single' model and scaler.")
            model.save(model_path)
            joblib.dump(scaler, scaler_path)
            
        predictions_scaled = []
        last_sequence = scaled_data[-look_back:]
        
        for _ in range(gap_length):
            pred = model.predict(last_sequence.reshape(1, look_back, 1), verbose=0)[0, 0]
            if data_char['has_many_spikes']:
                noise = np.random.normal(0, np.std(scaled_data) * 0.05)
                pred += noise
            predictions_scaled.append(pred)
            last_sequence = np.append(last_sequence[1:], pred)
            
        predictions = scaler.inverse_transform(np.array(predictions_scaled).reshape(-1, 1)).flatten()
        
        data_min, data_max = np.min(training_data), np.max(training_data)
        data_range = data_max - data_min
        predictions = np.clip(predictions, data_min - 0.3 * data_range, data_max + 0.3 * data_range)
        print(f"    -> Final predictions range: [{predictions.min():.2f}, {predictions.max():.2f}]")
        return predictions

    return None

def compare_imputation_results(original_df, imputed_df, context_points=5):
    """Compare original vs imputed data around each gap."""
    power_col = 'real_power' if 'real_power' in original_df.columns else 'power'
    
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
        
        context_start = max(0, start_idx - context_points)
        context_end = min(len(original_df), end_idx + 1 + context_points)
        
        original_context = original_df.iloc[context_start:context_end].copy()
        imputed_context = imputed_df.iloc[context_start:context_end].copy()
        
        original_context['Position'] = ['Before'] * (start_idx - context_start) + \
                                     ['GAP'] * gap_length + \
                                     ['After'] * (context_end - end_idx - 1)
        
        imputed_context['Position'] = ['Before'] * (start_idx - context_start) + \
                                    ['IMPUTED'] * gap_length + \
                                    ['After'] * (context_end - end_idx - 1)
        
        comparison = pd.DataFrame({
            'Index': range(context_start, context_end),
            'Original': original_context[power_col],
            'Imputed': imputed_context[power_col],
            'Position': original_context['Position'],
            'Difference': imputed_context[power_col] - original_context[power_col]
        })
        
        if isinstance(original_df.index, pd.DatetimeIndex):
            comparison['Timestamp'] = original_context.index
        
        print("\nComparison (Original vs Imputed):")
        print("-" * 60)
        
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
        
        comparison_results.append({
            'gap_number': i + 1,
            'start_idx': start_idx,
            'end_idx': end_idx,
            'comparison_df': comparison
        })
    
    return comparison_results

def create_before_after_plots(original_df, imputed_df, plot_name="power_data", save_html=True, output_dir="./"):
    """Create two line plots: one before imputation (with gaps) and one after imputation."""
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        import os
        
        power_col = 'real_power' if 'real_power' in original_df.columns else 'power'
        gaps = find_gaps(original_df)
        
        html_files = []
        
        if isinstance(original_df.index, pd.DatetimeIndex):
            timestamp_col = original_df.index
        else:
            if 'timestamp_x' in original_df.columns:
                timestamp_col = pd.to_datetime(original_df['timestamp_x'])
            else:
                raise ValueError("No timestamp_x column found. DataFrame must have DatetimeIndex or 'timestamp_x' column.")
        
        print(f"Creating 'Before Imputation' plot for {plot_name}...")
        
        before_plot_df = pd.DataFrame({
            'Timestamp': timestamp_col,
            'Real_Power': original_df[power_col].values
        })
        
        fig_before = px.line(before_plot_df, x='Timestamp', y='Real_Power', 
                            title=f"{plot_name} - Before Imputation (Original Data with Gaps)",
                            labels={'Timestamp': 'Timestamp', 'Real_Power': 'Real Power'})
        
        fig_before.update_traces(line=dict(color='blue', width=2))
        
        if len(gaps) > 0:
            y_min = original_df[power_col].min() * 0.95
            y_max = original_df[power_col].max() * 1.05
            
            for i, (start_idx, end_idx) in enumerate(gaps):
                gap_start_x = timestamp_col.iloc[start_idx]
                gap_end_x = timestamp_col.iloc[end_idx]
                
                fig_before.add_shape(
                    type="rect",
                    x0=gap_start_x, y0=y_min,
                    x1=gap_end_x, y1=y_max,
                    fillcolor="red", opacity=0.2,
                    layer="below", line_width=0
                )
                
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
        
        if save_html:
            filename_before = f"{plot_name}_before_imputation.html"
            filepath_before = os.path.join(output_dir, filename_before)
            fig_before.write_html(filepath_before)
            html_files.append(filepath_before)
            print(f"  -> Saved 'Before' plot to: {filepath_before}")
        
        print(f"Creating 'After Imputation' plot for {plot_name}...")
        
        after_plot_df = pd.DataFrame({
            'Timestamp': timestamp_col,
            'Real_Power': imputed_df[power_col].values
        })
        
        fig_after = px.line(after_plot_df, x='Timestamp', y='Real_Power',
                           title=f"{plot_name} - After Imputation (Complete Data)",
                           labels={'Timestamp': 'Timestamp', 'Real_Power': 'Real Power'})
        
        fig_after.update_traces(line=dict(color='green', width=2))
        
        if len(gaps) > 0:
            y_min = imputed_df[power_col].min() * 0.95
            y_max = imputed_df[power_col].max() * 1.05
            
            for i, (start_idx, end_idx) in enumerate(gaps):
                gap_start_x = timestamp_col.iloc[start_idx]
                gap_end_x = timestamp_col.iloc[end_idx]
                
                fig_after.add_shape(
                    type="rect",
                    x0=gap_start_x, y0=y_min,
                    x1=gap_end_x, y1=y_max,
                    fillcolor="yellow", opacity=0.3,
                    layer="below", line_width=1,
                    line_color="orange"
                )
                
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

def impute_power_gaps(df, small_gap_threshold=4, training_window=200, 
                     lstm_approach='auto', show_comparison=True, create_plots=True, 
                     plot_name="power_data", save_html=True, output_dir="./"):
    """Main imputation function with spike-aware LSTM approaches."""
    
    original_df = df.copy()
    df_processed = df.copy()
    
    if 'timestamp_x' in df_processed.columns:
        df_processed['timestamp_x'] = pd.to_datetime(df_processed['timestamp_x'])
        if not isinstance(df_processed.index, pd.DatetimeIndex):
            df_processed.set_index('timestamp_x', inplace=True)
    
    if 'real_power' in df_processed.columns:
        power_col = 'real_power'
    elif 'power' in df_processed.columns:
        power_col = 'power'
    else:
        raise ValueError("DataFrame must have 'real_power' or 'power' column")
    
    print(f"Number of NaN values: {df_processed[power_col].isna().sum()}")
    
    gaps = find_gaps(df_processed)
    print(f"Found {len(gaps)} gaps to process.")
    
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
                df_processed[power_col].fillna(method='ffill', inplace=True)
                df_processed[power_col].fillna(method='bfill', inplace=True)
        
        else:
            print(f"  -> Using spike-aware LSTM imputation (approach: {lstm_approach})")
            imputation_method = f"LSTM_{lstm_approach}"
            
            training_data = []
            
            before_start = max(0, start_idx - training_window)
            before_data = df_processed[power_col].iloc[before_start:start_idx].dropna()
            if len(before_data) > 0:
                training_data.extend(before_data.values)
            
            after_end = min(len(df_processed), end_idx + 1 + training_window)
            after_data = df_processed[power_col].iloc[end_idx + 1:after_end].dropna()
            if len(after_data) > 0:
                training_data.extend(after_data.values)
            
            training_data = np.array(training_data)
            
            if len(training_data) >= 80:  # Increased minimum requirement
                predictions = train_and_predict_spike_aware_lstm(training_data, gap_length, approach=lstm_approach)
                
                if predictions is not None:
                    predictions=abs(predictions)
                    df_processed[power_col].iloc[start_idx:end_idx + 1] = predictions
                    print(f"  -> Successfully imputed {gap_length} values using spike-aware LSTM")
                else:
                    print("  -> Spike-aware LSTM failed, using linear interpolation as fallback")
                    imputation_method = "linear_fallback"
                    if start_idx > 0 and end_idx < len(df_processed) - 1:
                        before_val = df_processed[power_col].iloc[start_idx - 1]
                        after_val = df_processed[power_col].iloc[end_idx + 1]
                        interpolated_values = np.linspace(before_val, after_val, gap_length + 2)[1:-1]
                        df_processed[power_col].iloc[start_idx:end_idx + 1] = interpolated_values
            else:
                print(f"  -> Insufficient training data ({len(training_data)} points), using linear interpolation")
                imputation_method = "linear_fallback"
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
    
    comparison_results = None
    if show_comparison and len(gaps) > 0:
        comparison_results = compare_imputation_results(original_df, df_processed)
    
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

if __name__ == '__main__':
    print("=== Spike-Aware LSTM Power Data Imputation Tool ===\n")
    
    df_sample = pd.read_csv(files[0], usecols = ['timestamp_x', 'real_power'])
    
    print("\n" + "="*60)
    print("STARTING SPIKE-AWARE IMPUTATION PROCESS")
    print("="*60)
    
    # Available approaches: 'auto', 'ensemble', 'residual', 'enhanced_single'
    approach = 'auto'  # Let the system choose based on data characteristics
    
    for file in files:
        name = file.name.split('.')[0]
        print(f"\nProcessing file: {name}")
        
        df_sample = pd.read_csv(file)
        df_sample = df_sample.drop(columns = ['is_zero', 'true_zero'])
        
        result_df, gap_info, _ = impute_power_gaps(
            df_sample.copy(), 
            small_gap_threshold=4,           
            training_window=200,             # Increased training window
            lstm_approach=approach,          # New parameter for LSTM approach
            show_comparison=False,           
            create_plots=True,              # Disable plotting
            plot_name=name,
            save_html=True,                 # Disable HTML saving
            output_dir="./csv-plot-output"                  
        )
        
        # Save the imputed DataFrame to CSV
        output_filename = f"{name}_imputed.csv"
        output_filepath = os.path.join(output_csv_dir, output_filename)
        
        # Save to CSV with proper formatting
        result_df.to_csv(
            output_filepath, 
            index=True,           # Keep index if it contains timestamps
            encoding='utf-8',     # Use UTF-8 encoding
            na_rep=''            # Replace any remaining NaN with empty string
        )
        
        print(f"   Imputed data saved to: {output_filepath}")
        print(f"   Original NaN count: {df_sample['real_power'].isna().sum()}")
        print(f"   Final NaN count: {result_df['real_power'].isna().sum()}")
        
        # Print gap processing summary for this file
        print(f"\n📊 Gap Processing Summary for {name}:")
        if gap_info:
            for gap in gap_info:
                print(f"    Gap {gap['gap_number']}: Length {gap['length']} -> Method: {gap['method']}")
        else:
            print("    No gaps found in this file")
    
    print("\n" + "="*60)
    print("SPIKE-AWARE IMPUTATION COMPLETE")
    print("="*60)
    
    print(f"\n All imputed CSV files saved to: {output_csv_dir}/")
    print(" Files created:")
    
    # List all created files
    for file in Path(output_csv_dir).iterdir():
        if file.is_file() and file.suffix == '.csv':
            print(f"   - {file.name}")
    
    print("\n Spike-aware imputation process completed successfully!")


# # Example usage and testing
# if __name__ == '__main__':
#     print("=== Spike-Aware LSTM Power Data Imputation Tool ===\n")
    
#     df_sample = pd.read_csv(files[0], usecols = ['timestamp_x', 'real_power'])
    
#     print("\n" + "="*60)
#     print("STARTING SPIKE-AWARE IMPUTATION PROCESS")
#     print("="*60)
    
#     # Available approaches: 'auto', 'ensemble', 'residual', 'enhanced_single'
#     approach = 'auto'  # Let the system choose based on data characteristics
    
#     for file in files:
#         name = file.name.split('.')[0]
#         df_sample = pd.read_csv(file, usecols = ['timestamp_x', 'real_power'])
#         result_df, gap_info, html_files = impute_power_gaps(
#             df_sample.copy(), 
#             small_gap_threshold=4,           
#             training_window=200,             # Increased training window
#             lstm_approach=approach,          # New parameter for LSTM approach
#             show_comparison=False,            
#             create_plots=True,               
#             plot_name=name,
#             save_html=True,                  
#             output_dir="./csv-plot-output"                  
#         )
    
#     print("\n" + "="*60)
#     print("SPIKE-AWARE IMPUTATION COMPLETE")
#     print("="*60)
    
#     print(f"\nGap Processing Summary:")
#     for gap in gap_info:
#         print(f"  Gap {gap['gap_number']}: Length {gap['length']} -> Method: {gap['method']}")
    
#     if html_files:
#         print(f"\nVisualization files created:")
#         for file in html_files:
#             print(f"  - {file}")
#         print("\nSpike-aware LSTM should now much better handle spiky data patterns!")
#         print("Open these HTML files in your browser to view the results!")
    
#     print(f"\nFinal result: {result_df['real_power'].isna().sum()} remaining NaN values")
#     print("Spike-aware imputation process completed successfully!")