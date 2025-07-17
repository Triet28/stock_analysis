import pandas as pd

def calculate_support(df: pd.DataFrame) -> pd.DataFrame:
    """Tính toán điểm hỗ trợ dựa trên giá đóng cửa trong toàn bộ khoảng thời gian"""
    df['Support'] = df['Close'].min()
    return df