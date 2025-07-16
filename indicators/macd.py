import pandas as pd
from ta.trend import MACD

def calculate_macd(df: pd.DataFrame, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9) -> pd.DataFrame:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Parameters:
    - fast_period: EMA fast period (default: 12)
    - slow_period: EMA slow period (default: 26)  
    - signal_period: Signal line EMA period (default: 9)
    
    Returns:
    - DataFrame with MACD, Signal, and Histogram columns
    """
    df = df.copy()
    
    # Calculate MACD using ta library
    macd_indicator = MACD(close=df['Close'], 
                         window_slow=slow_period, 
                         window_fast=fast_period, 
                         window_sign=signal_period)
    
    # MACD line = EMA12 - EMA26
    df['MACD'] = macd_indicator.macd()
    
    # Signal line = EMA9 of MACD
    df['MACD_Signal'] = macd_indicator.macd_signal()
    
    # Histogram = MACD - Signal
    df['MACD_Histogram'] = macd_indicator.macd_diff()
    
    return df
