import pandas as pd

def calculate_ichimoku(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Ichimoku Cloud indicators"""
    df = df.copy()
    
    # Tenkan-sen (Conversion Line): (High9 + Low9) / 2
    df['ICH_Tenkan'] = ((df['High'].rolling(window=9).max() + df['Low'].rolling(window=9).min()) / 2)
    
    # Kijun-sen (Base Line): (High26 + Low26) / 2
    df['ICH_Kijun'] = ((df['High'].rolling(window=26).max() + df['Low'].rolling(window=26).min()) / 2)
    
    # Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, shifted 26 periods forward
    df['ICH_SpanA'] = ((df['ICH_Tenkan'] + df['ICH_Kijun']) / 2).shift(26)
    
    # Senkou Span B (Leading Span B): (High52 + Low52) / 2, shifted 26 periods forward  
    df['ICH_SpanB'] = ((df['High'].rolling(window=52).max() + df['Low'].rolling(window=52).min()) / 2).shift(26)
    
    # Chikou Span (Lagging Span): Close price shifted 26 periods backward
    df['ICH_Chikou'] = df['Close'].shift(-26)
    
    return df
