import warnings
import numpy as np
import pandas as pd
import time
import pickle
import json
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from xgboost import XGBRegressor

# XGBoost Momentum Model - Training & Artifact Generation Script
# Author: John Swindell

# # 1. Imports & Global Settings
warnings.simplefilter(action='ignore', category=FutureWarning)

# # 2. Data Loading & Initial Preparation
print("--- Section 2: Data Loading & Initial Preparation ---")
df = pd.read_parquet('crypto_market_data.parquet')
df['date'] = pd.to_datetime(df['date'])
df.sort_values(by=['ticker', 'date'], inplace=True)
df.reset_index(drop=True, inplace=True)
print("Data loaded and prepared successfully.")


# # 3. Feature Engineering
print("\n--- Section 3: Feature Engineering ---")

# --- Original Price & TA Features ---
lookback_periods = [7, 10, 14, 21, 30, 42, 60]
for period in lookback_periods:
    df[f'ret_{period}d'] = df.groupby('ticker')['price'].pct_change(periods=period)

df['ret_1d'] = df.groupby('ticker')['price'].pct_change(periods=1)
df['volatility_14d'] = df.groupby('ticker')['ret_1d'].rolling(window=14).std().reset_index(level=0, drop=True)

rolling_mean_vol = df.groupby('ticker')['volume'].rolling(window=14).mean().reset_index(level=0, drop=True)
rolling_std_vol = df.groupby('ticker')['volume'].rolling(window=14).std().reset_index(level=0, drop=True)
df['volume_zscore_14d'] = (df['volume'] - rolling_mean_vol) / rolling_std_vol

df['rsi_14'] = df.groupby('ticker')['price'].transform(lambda x: RSIIndicator(close=x, window=14).rsi())
df['bb_width'] = df.groupby('ticker')['price'].transform(lambda x: BollingerBands(close=x, window=20).bollinger_wband())
df['bb_percent_b'] = df.groupby('ticker')['price'].transform(lambda x: BollingerBands(close=x, window=20).bollinger_pband())
df['macd_diff'] = df.groupby('ticker')['price'].transform(lambda x: MACD(close=x, window_slow=26, window_fast=12, window_sign=9).macd_diff())

# --- Market Regime Filter (Calculation on Full Dataset) ---
print("Calculating market regime filter...")
btc_df = df[df['ticker'] == 'BTC'][['date', 'price']].copy().set_index('date')
btc_df['ma_200d'] = btc_df['price'].rolling(window=200).mean()
btc_df['market_regime'] = btc_df['price'] > btc_df['ma_200d']
df = df.merge(btc_df[['market_regime']], on='date', how='left')

# --- Interaction Features ---
print("Creating interaction features...")
df['mom_x_vol_42d'] = df['ret_42d'] * df['volatility_14d']

# --- Market-Neutral Momentum Features ---
print("Creating market-neutral momentum features...")
btc_returns = df[df['ticker'] == 'BTC'].set_index('date')
market_return_cols = [f'ret_{p}d' for p in [1] + lookback_periods]
btc_returns = btc_returns[market_return_cols]
df = df.merge(btc_returns.add_suffix('_btc'), on='date', how='left')
for period in [1] + lookback_periods:
    df[f'ret_{period}d_neutral'] = df[f'ret_{period}d'] - df[f'ret_{period}d_btc']
df.drop(columns=[col + '_btc' for col in market_return_cols], inplace=True)

print("Feature engineering complete.")

# # 4. Preprocessing & Model Preparation
print("\n--- Section 4: Preprocessing & Model Preparation ---")
features = [
    'ret_7d', 'ret_10d', 'ret_14d', 'ret_21d', 'ret_30d', 'ret_42d', 'ret_60d',
    'volatility_14d', 'volume_zscore_14d', 'rsi_14', 'bb_width', 'bb_percent_b', 'macd_diff',
    'mom_x_vol_42d',
    'ret_1d_neutral', 'ret_7d_neutral', 'ret_10d_neutral', 'ret_14d_neutral',
    'ret_21d_neutral', 'ret_30d_neutral', 'ret_42d_neutral', 'ret_60d_neutral'
]
df['target'] = df.groupby('ticker')['price'].pct_change(periods=7).shift(-7)
df.dropna(subset=features + ['target'], inplace=True)
df.sort_values('date', inplace=True)

split_index = int(len(df) * 0.8)
cutoff_date = df.iloc[split_index]['date']
train_df = df[df['date'] < cutoff_date].copy()

X_train_raw = train_df[features]
y_train = train_df['target']

# --- Vectorized Point-in-Time Processing for Training Data ---
print("\nStarting vectorized point-in-time processing of training data...")
min_window_size = 180
lower_bounds = X_train_raw.expanding(min_periods=min_window_size).quantile(0.01)
upper_bounds = X_train_raw.expanding(min_periods=min_window_size).quantile(0.99)
X_train_winsorized = X_train_raw.clip(lower=lower_bounds.shift(1), upper=upper_bounds.shift(1), axis=1)

expanding_median = X_train_raw.expanding(min_periods=min_window_size).median()
expanding_q1 = X_train_raw.expanding(min_periods=min_window_size).quantile(0.25)
expanding_q3 = X_train_raw.expanding(min_periods=min_window_size).quantile(0.75)
expanding_iqr = expanding_q3 - expanding_q1
X_train_processed = (X_train_winsorized - expanding_median.shift(1)) / expanding_iqr.shift(1)

X_train_processed.replace([np.inf, -np.inf], np.nan, inplace=True)
X_train_processed.fillna(0, inplace=True)
X_train_processed.dropna(inplace=True)
y_train_processed = y_train[X_train_processed.index]
print("Training data processing complete.")


# # 5. Model Training (XGBoost)
print("\n--- Section 5: Model Training (XGBoost) ---")
print("Setting up Walk-Forward Cross-Validation and Hyperparameter Tuning for XGBoost...")
param_search_space = {
    'learning_rate': [0.03, 0.05, 0.1],
    'max_depth': [2, 3, 4],
    'n_estimators': [200, 400, 600],
    'subsample': [0.7, 0.8],
    'colsample_bytree': [0.7, 0.8],
    'reg_lambda': [5, 10, 20],
    'gamma': [0, 1, 5]
}
tscv = TimeSeriesSplit(n_splits=5)
model = XGBRegressor(objective='reg:squarederror', random_state=42, n_jobs=-1)
grid_search = RandomizedSearchCV(
    estimator=model, param_distributions=param_search_space,
    n_iter=25, scoring='neg_root_mean_squared_error',
    cv=tscv, verbose=2, n_jobs=-1
)
print("Training XGBoost model...")
start_time = time.time()
grid_search.fit(X_train_processed, y_train_processed)
end_time = time.time()
print(f"Grid search complete. Took {end_time - start_time:.2f} seconds.")
print("\nBest parameters found: ", grid_search.best_params_)


# # 6. Generate Deployment Artifacts
print("\n--- Section 6: Generate Deployment Artifacts ---")

# 1. Get the best model from the grid search
best_model = grid_search.best_estimator_

# 2. Define the final preprocessing objects fitted on the entire raw training data
final_lower_bounds = X_train_raw.quantile(0.01)
final_upper_bounds = X_train_raw.quantile(0.99)
# Note: Fit scaler on the winsorized data, as that's what the model was trained on
final_scaler = RobustScaler().fit(X_train_raw.clip(lower=final_lower_bounds, upper=final_upper_bounds, axis=1))

# 3. Create a dictionary to hold all the artifacts for deployment
artifacts = {
    'model': best_model,
    'scaler': final_scaler,
    'lower_bounds': final_lower_bounds,
    'upper_bounds': final_upper_bounds,
    'feature_names': features
}

# 4. Save the artifacts dictionary to a single .pkl file
artifacts_filename = 'model_artifacts.pkl'
with open(artifacts_filename, 'wb') as file:
    pickle.dump(artifacts, file)
print(f"✅ Model and preprocessors saved to '{artifacts_filename}'")

# 5. Create and save a sample payload for API testing
# This will show you guys on the backend team the exact input format the model expects 👍
sample_payload_df = X_train_processed.head(1)
sample_payload = sample_payload_df.to_dict(orient='records')[0]

payload_filename = 'sample_prediction_payload.json'
with open(payload_filename, 'w') as file:
    json.dump(sample_payload, file, indent=4)
print(f"✅ Example prediction payload saved to '{payload_filename}'")