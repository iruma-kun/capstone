import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.ensemble import RandomForestRegressor
from datetime import datetime, timedelta

class StockForecaster:
    """
    A machine learning time-series forecasting model for asset prices.
    Uses rolling indicators and an MLP Neural Network or Random Forest to forecast N-day returns.
    """

    def __init__(self, ticker: str, forecast_days: int = 5):
        self.ticker = ticker
        self.forecast_days = forecast_days
        self.model = MLPRegressor(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            max_iter=500,
            random_state=42
        )
        # Fallback model in case neural network convergence fails or is slow
        self.fallback_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False

    def fetch_data(self, period: str = "2y") -> pd.DataFrame:
        """Fetches historical price data from Yahoo Finance."""
        ticker_obj = yf.Ticker(self.ticker)
        # Fetch price history
        df = ticker_obj.history(period=period)
        if df.empty:
            raise ValueError(f"No historical price data found for ticker {self.ticker}")
        return df

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes technical indicators for training features."""
        data = df.copy()

        # Base indicators
        data['Returns'] = data['Close'].pct_change()

        # Moving Averages
        data['MA_5'] = data['Close'].rolling(window=5).mean()
        data['MA_20'] = data['Close'].rolling(window=20).mean()
        data['MA_50'] = data['Close'].rolling(window=50).mean()

        # Volatility (Rolling standard deviation)
        data['Vol_5'] = data['Returns'].rolling(window=5).std()
        data['Vol_20'] = data['Returns'].rolling(window=20).std()

        # Momentum (RSI estimate)
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        data['RSI_14'] = 100 - (100 / (1 + rs))

        # Log difference to make price stationary
        data['Log_Close'] = np.log(data['Close'])
        data['Log_Diff'] = data['Log_Close'].diff()

        # Lagged features
        for lag in [1, 2, 3, 5, 10]:
            data[f'Lag_{lag}_Ret'] = data['Returns'].shift(lag)
            data[f'Lag_{lag}_Vol'] = data['Vol_5'].shift(lag)

        # Target variable: Future Return over next N days
        # E.g. we want to predict the % price change N days from now
        data['Target'] = data['Close'].shift(-self.forecast_days) / data['Close'] - 1.0

        # Clean up NaNs created by rolling indicators and shifts
        data = data.dropna()

        return data

    def train(self, data: pd.DataFrame) -> dict:
        """Trains the ML models on the engineered features."""
        # Define feature columns
        feature_cols = [
            'Returns', 'MA_5', 'MA_20', 'MA_50', 'Vol_5', 'Vol_20', 'RSI_14',
            'Lag_1_Ret', 'Lag_1_Vol', 'Lag_2_Ret', 'Lag_2_Vol',
            'Lag_3_Ret', 'Lag_3_Vol', 'Lag_5_Ret', 'Lag_5_Vol'
        ]

        # Ensure features are in the dataset
        X = data[feature_cols].values
        y = data['Target'].values

        # Split into training and testing (80/20 sequential split for time-series)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train MLP Neural Network
        try:
            self.model.fit(X_train_scaled, y_train)
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)
            self.is_trained = True
            active_model = "MLP"
        except Exception as e:
            # Fall back to Random Forest if MLP fails
            self.fallback_model.fit(X_train, y_train)
            train_score = self.fallback_model.score(X_train, y_train)
            test_score = self.fallback_model.score(X_test, y_test)
            self.is_trained = True
            active_model = "RandomForest"

        return {
            "model_type": active_model,
            "train_r2": round(train_score, 4),
            "test_r2": round(test_score, 4),
            "data_points": len(X)
        }

    def predict_next(self, current_data: pd.DataFrame) -> dict:
        """Forecasts the future price and percentage move."""
        if not self.is_trained:
            raise ValueError("Model must be trained before predicting.")

        feature_cols = [
            'Returns', 'MA_5', 'MA_20', 'MA_50', 'Vol_5', 'Vol_20', 'RSI_14',
            'Lag_1_Ret', 'Lag_1_Vol', 'Lag_2_Ret', 'Lag_2_Vol',
            'Lag_3_Ret', 'Lag_3_Vol', 'Lag_5_Ret', 'Lag_5_Vol'
        ]

        # Grab the very latest data row to make future prediction
        latest_row = current_data.iloc[-1]
        X_latest = latest_row[feature_cols].values.reshape(1, -1)

        # Predict percentage move
        if hasattr(self, 'model') and getattr(self, 'is_trained') and not isinstance(self.model, RandomForestRegressor):
            X_latest_scaled = self.scaler.transform(X_latest)
            predicted_return = self.model.predict(X_latest_scaled)[0]
        else:
            predicted_return = self.fallback_model.predict(X_latest)[0]

        current_price = latest_row['Close']
        predicted_price = current_price * (1.0 + predicted_return)

        return {
            "ticker": self.ticker,
            "current_price": round(current_price, 2),
            "predicted_price": round(predicted_price, 2),
            "predicted_return": round(predicted_return, 4),
            "direction": "UP" if predicted_return > 0 else "DOWN",
            "forecast_horizon_days": self.forecast_days
        }

def run_pipeline(ticker: str, forecast_days: int = 5) -> dict:
    """Convenience helper to run the full data, train, and prediction pipeline."""
    try:
        forecaster = StockForecaster(ticker, forecast_days)
        raw_data = forecaster.fetch_data()
        engineered = forecaster.engineer_features(raw_data)
        metrics = forecaster.train(engineered)
        prediction = forecaster.predict_next(engineered)

        return {
            "success": True,
            "metrics": metrics,
            "prediction": prediction
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    print("Testing ML Forecaster pipeline for AAPL...")
    # Apple (AAPL)
    result = run_pipeline("AAPL", forecast_days=5)
    print("Pipeline Result:")
    import json
    print(json.dumps(result, indent=2))
