import pandas as pd

def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate moving averages (MA10, MA50, MA100, MA200)"""
    df = df.copy()
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA100'] = df['Close'].rolling(window=100).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    return df
