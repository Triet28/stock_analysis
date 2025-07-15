import pandas as pd
from ta.volatility import BollingerBands

def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, window_dev: int = 2) -> pd.DataFrame:
    """Calculate Bollinger Bands"""
    df = df.copy()
    bb = BollingerBands(close=df['Close'], window=window, window_dev=window_dev)
    df['BB_Upper'] = bb.bollinger_hband()
    df['BB_Lower'] = bb.bollinger_lband()
    df['BB_Middle'] = bb.bollinger_mavg()
    return df
