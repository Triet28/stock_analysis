import pandas as pd

def calculate_resistance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán điểm kháng cự dựa trên giá đóng cửa trong toàn bộ khoảng thời gian"""
    df['Resistance'] = df['Close'].max()
    return df