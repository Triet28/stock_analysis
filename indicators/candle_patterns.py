import pandas as pd
import numpy as np
from typing import List, Dict
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.trend_analysis import calculate_trend

def _map_trends_to_dataframe(df: pd.DataFrame, trends: List[Dict]) -> pd.DataFrame:
    """
    Map xu hướng từ trend_analysis vào DataFrame để phân loại candle patterns
    
    Args:
        df: DataFrame với cột Date, Open, High, Low, Close
        trends: Danh sách xu hướng từ trend_analysis
        
    Returns:
        DataFrame với cột 'trend_context' mới
    """
    df_result = df.copy()
    
    # Chuyển đổi Date về datetime nếu cần
    if df_result['Date'].dtype == 'object':
        df_result['Date'] = pd.to_datetime(df_result['Date'], format='%d/%m/%Y')
    
    # Tạo cột xu hướng mặc định
    df_result['trend_context'] = 'sideways'
    
    # Map xu hướng từ trend_analysis vào từng ngày
    for trend in trends:
        trend_start = pd.to_datetime(trend['period'].split(' to ')[0], format='%d/%m/%Y')
        trend_end = pd.to_datetime(trend['period'].split(' to ')[1], format='%d/%m/%Y')
        
        # Gán xu hướng cho tất cả ngày trong khoảng thời gian này
        # Chuyển về lowercase để đồng nhất
        trend_value = trend['trend'].lower()
        mask = (df_result['Date'] >= trend_start) & (df_result['Date'] <= trend_end)
        df_result.loc[mask, 'trend_context'] = trend_value
    
    return df_result

def classify_candle_pattern(df: pd.DataFrame, exchange: str, trends: List[Dict] = None) -> pd.DataFrame:
    df_result = df.copy()
    df_result['candle_pattern'] = 'Standard'
    
    # Lưu lại format Date gốc
    original_date_format = df_result['Date'].dtype == 'object'
    original_dates = df_result['Date'].copy()
    
    # Tính toán các giá trị cần thiết
    df_result['body_size'] = abs(df_result['Close'] - df_result['Open'])
    df_result['upper_shadow'] = df_result['High'] - df_result[['Open', 'Close']].max(axis=1)
    df_result['lower_shadow'] = df_result[['Open', 'Close']].min(axis=1) - df_result['Low']
    df_result['total_range'] = df_result['High'] - df_result['Low']
    df_result['body_percentage'] = (abs(df_result['Close'] - df_result['Open']) / df_result['Open']) * 100
    # Tính toán ngưỡng cho việc phân loại

    df_result['body_ratio'] = df_result['body_size'] / df_result['total_range']
    df_result['upper_shadow_ratio'] = df_result['upper_shadow'] / df_result['total_range']
    df_result['lower_shadow_ratio'] = df_result['lower_shadow'] / df_result['total_range']
    
    # Xác định loại nến (xanh/đỏ)
    df_result['is_green'] = df_result['Close'] > df_result['Open']
    
    # Sử dụng xu hướng từ trend_analysis hoặc tự động phân tích
    
    # Map xu hướng vào DataFrame
    if trends:
        df_result = _map_trends_to_dataframe(df_result, trends)
    else:
        # Fallback: không có xu hướng, tất cả sẽ được phân loại là sideways
        df_result['trend_context'] = 'sideways'
    
    # Khôi phục lại Date format gốc nếu cần
    if original_date_format:
        df_result['Date'] = original_dates
    
    # Ngưỡng phân loại
    SMALL_BODY_THRESHOLD = 0.1      # Thân nến nhỏ
    SMALL_SHADOW_THRESHOLD = 0.05   # Râu ngắn
    LARGE_SHADOW_THRESHOLD = 0.3    # Râu dài
    DOJI_THRESHOLD = 0.03           # Ngưỡng cho Doji
    
    # Ngưỡng Marubozu theo sàn giao dịch
    if exchange == "HSX":
        MARUBOZU_THRESHOLD = 3      # 3% movement cho HSX
    elif exchange == "HNX":
        MARUBOZU_THRESHOLD = 5      # 5% movement cho HNX
    elif exchange== "UPCOM":
        MARUBOZU_THRESHOLD = 7      # 7% movement cho UPCOM
    else:
        MARUBOZU_THRESHOLD = 3      # Mặc định HSX nếu không xác định được sàn
    
    for idx in df_result.index:
        row = df_result.loc[idx]
        trend = row.get('trend_context', 'sideways').lower()  # Chuyển về lowercase để match
        
        # 1. Nến Doji và các biến thể (ưu tiên cao nhất)
        if row['body_ratio'] <= DOJI_THRESHOLD:
            # Star Doji - râu ngắn, gần bằng nhau
            if (row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and 
                row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and 
                abs(row['lower_shadow_ratio'] - row['upper_shadow_ratio']) <= 0.02):
                df_result.loc[idx, 'candle_pattern'] = 'Star Doji'
            
            # Long Legged Doji - cả 2 râu đều dài và gần bằng nhau
            elif (abs(row['upper_shadow_ratio'] - row['lower_shadow_ratio']) <= 0.1 and
                  row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
                  row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                df_result.loc[idx, 'candle_pattern'] = 'Long Legged Doji'
            
            # Dragonfly Doji - râu trên ngắn, râu dưới dài
            elif (row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
                    row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                if row['trend_context'] == 'downtrend':
                    df_result.loc[idx, 'candle_pattern'] = 'Dragonfly Doji'
                elif row['trend_context'] == 'uptrend':
                    df_result.loc[idx, 'candle_pattern'] = 'Hanging Man'
            # Gravestone Doji
            elif (row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
                  row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                if row['trend_context'] == 'uptrend':
                    df_result.loc[idx, 'candle_pattern'] = 'Gravestone Doji'
                elif row['trend_context'] == 'downtrend':
                    df_result.loc[idx, 'candle_pattern'] = 'Inverted Hammer'
        
        # 2. Nến Marubozu - thân lớn, râu ngắn, không phụ thuộc trend
        elif (row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
              row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
              row['body_percentage'] >= MARUBOZU_THRESHOLD):
            df_result.loc[idx, 'candle_pattern'] = 'Marubozu'
        
        # 3. Hammer/Hanging Man - thân nhỏ, râu dưới dài, râu trên ngắn
        elif (row['body_ratio'] <= SMALL_BODY_THRESHOLD and
              row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
              row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD):
            if trend == 'downtrend':
                df_result.loc[idx, 'candle_pattern'] = 'Hammer'
            elif trend == 'uptrend':
                df_result.loc[idx, 'candle_pattern'] = 'Hanging Man'
            # Nếu sideways, không phân loại thành pattern đặc biệt
        
        # 4. Inverted Hammer/Shooting Star - thân nhỏ, râu trên dài, râu dưới ngắn
        elif (row['body_ratio'] <= SMALL_BODY_THRESHOLD and
              row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
              row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD):
            if trend == 'downtrend':
                df_result.loc[idx, 'candle_pattern'] = 'Inverted Hammer'
            elif trend == 'uptrend':
                df_result.loc[idx, 'candle_pattern'] = 'Shooting Star'
    return df_result

def detect_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Phát hiện Rising/Falling Windows (gaps)
    
    Args:
        df: DataFrame với cột Open, High, Low, Close đã sắp xếp theo thời gian
        
    Returns:
        DataFrame với cột 'gap_type' mới
    """
    df_result = df.copy()
    df_result['gap_type'] = 'No Gap'
    
    for i in range(1, len(df_result)):
        current_open = df_result.iloc[i]['Open']
        previous_high = df_result.iloc[i-1]['High']
        previous_low = df_result.iloc[i-1]['Low']
        
        # Gap tăng (Up Gap/Rising Window)
        # Điều kiện: Giá mở cửa > giá cao nhất của nến trước đó
        if current_open > previous_high:
            df_result.iloc[i, df_result.columns.get_loc('gap_type')] = 'Rising Window'
        
        # Gap giảm (Down Gap/Falling Window)  
        # Điều kiện: Giá mở cửa < giá thấp nhất của nến trước đó
        elif current_open < previous_low:
            df_result.iloc[i, df_result.columns.get_loc('gap_type')] = 'Falling Window'
    
    return df_result

def get_candle_statistics(df: pd.DataFrame) -> Dict:
    """
    Thống kê các loại nến trong DataFrame
    
    Args:
        df: DataFrame với cột 'candle_pattern'
        
    Returns:
        Dict chứa thống kê các loại nến
    """
    if 'candle_pattern' not in df.columns:
        return {"error": "DataFrame không có cột 'candle_pattern'"}
    
    filtered_df = df[df['candle_pattern'] != 'Standard']
    pattern_counts = filtered_df['candle_pattern'].value_counts().to_dict()
    total_special_candles = len(filtered_df)
    total_candles = len(df)
    pattern_percentages = {
        pattern: {
            "count": count,
            "percentage": round((count / total_candles) * 100, 2)
        }
        for pattern, count in pattern_counts.items()
    }
    
    return {
        "total_special_candles": total_special_candles,
        "pattern_distribution": pattern_percentages,
        # "most_common_pattern": max(pattern_counts, key=pattern_counts.get),
        "pattern_types": list(pattern_counts.keys())
    }

def analyze_candle_patterns(df: pd.DataFrame, trends: List[Dict] = None, exchange: str = "HSX") -> Dict:
    """
    Phân tích toàn diện các mẫu nến
    
    Args:
        df: DataFrame với OHLC data
        trends: Danh sách xu hướng từ trend_analysis (optional)
        exchange: Sàn giao dịch để xác định ngưỡng Marubozu (HSX/HNX/UPCOM)
        
    Returns:
        Dict chứa phân tích chi tiết
    """
    # Phân loại nến với trends và exchange
    df_with_patterns = classify_candle_pattern(df, exchange, trends)
    
    # Phát hiện gaps
    df_with_gaps = detect_gaps(df_with_patterns)
    
    # Thống kê
    candle_stats = get_candle_statistics(df_with_gaps)
    
    # Thống kê gaps
    gap_counts = df_with_gaps['gap_type'].value_counts().to_dict()
    
    return {
        "candle_analysis": candle_stats,
        "gap_analysis": {
            "gap_distribution": gap_counts,
            "total_gaps": sum(count for gap_type, count in gap_counts.items() if gap_type != 'No Gap'),
            "rising_windows": gap_counts.get('Rising Window', 0),
            "falling_windows": gap_counts.get('Falling Window', 0)
        }
    }
