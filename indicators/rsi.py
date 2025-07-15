import pandas as pd
from ta.momentum import RSIIndicator

def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """Calculate RSI (Relative Strength Index)"""
    df = df.copy()
    rsi = RSIIndicator(close=df['Close'], window=window)
    df['RSI'] = rsi.rsi()
    return df
