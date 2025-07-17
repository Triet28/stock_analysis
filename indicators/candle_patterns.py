import pandas as pd
import numpy as np
from typing import List, Dict

def _calculate_weekly_trend_for_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính xu hướng theo tuần cho việc phân loại candle patterns
    
    Args:
        df: DataFrame với cột Date, Open, High, Low, Close
        
    Returns:
        DataFrame với cột 'weekly_trend' mới
    """
    df_result = df.copy()
    
    # Chuyển đổi Date về datetime nếu cần
    if df_result['Date'].dtype == 'object':
        df_result['Date'] = pd.to_datetime(df_result['Date'], format='%d/%m/%Y')
    
    # Thêm cột week để nhóm theo tuần
    df_result['Week'] = df_result['Date'].dt.isocalendar().week
    df_result['Year'] = df_result['Date'].dt.year
    df_result['WeekYear'] = df_result['Year'].astype(str) + '_' + df_result['Week'].astype(str)
    
    # Tạo cột xu hướng tuần
    df_result['weekly_trend'] = 'sideways'
    
    # Nhóm theo tuần và tính xu hướng
    for week_year, week_data in df_result.groupby('WeekYear'):
        if len(week_data) < 1:
            continue
        
        # Sắp xếp theo ngày trong tuần
        week_data_sorted = week_data.sort_values('Date')
        
        # Lấy giá đóng cửa đầu tuần và cuối tuần
        first_close = week_data_sorted.iloc[0]['Close']
        last_close = week_data_sorted.iloc[-1]['Close']
        
        # Tính phần trăm thay đổi
        if first_close != 0:
            percent_change = ((last_close - first_close) / first_close) * 100
        else:
            percent_change = 0
        
        # Xác định xu hướng tuần
        if percent_change >= 1:
            trend = 'uptrend'
        elif percent_change <= -1:
            trend = 'downtrend'
        else:
            trend = 'sideways'
        
        # Gán xu hướng cho tất cả các ngày trong tuần
        df_result.loc[week_data.index, 'weekly_trend'] = trend
    
    return df_result

def classify_candle_pattern(df: pd.DataFrame) -> pd.DataFrame:
    df_result = df.copy()
    df_result['candle_pattern'] = 'Standard'
    
    # Tính toán các giá trị cần thiết
    df_result['body_size'] = abs(df_result['Close'] - df_result['Open'])
    df_result['upper_shadow'] = df_result['High'] - df_result[['Open', 'Close']].max(axis=1)
    df_result['lower_shadow'] = df_result[['Open', 'Close']].min(axis=1) - df_result['Low']
    df_result['total_range'] = df_result['High'] - df_result['Low']
    
    # Tính toán ngưỡng cho việc phân loại
    df_result['body_ratio'] = df_result['body_size'] / df_result['total_range']
    df_result['upper_shadow_ratio'] = df_result['upper_shadow'] / df_result['total_range']
    df_result['lower_shadow_ratio'] = df_result['lower_shadow'] / df_result['total_range']
    
    # Xác định loại nến (xanh/đỏ)
    df_result['is_green'] = df_result['Close'] > df_result['Open']
    
    # Tính xu hướng theo tuần để phân biệt Hammer/Hanging Man và Inverted Hammer/Shooting Star
    df_result = _calculate_weekly_trend_for_patterns(df_result)
    
    # Ngưỡng phân loại
    SMALL_BODY_THRESHOLD = 0.1      # Thân nến nhỏ
    LARGE_BODY_THRESHOLD = 0.7      # Thân nến lớn
    SMALL_SHADOW_THRESHOLD = 0.05   # Râu ngắn
    LARGE_SHADOW_THRESHOLD = 0.4    # Râu dài
    DOJI_THRESHOLD = 0.03           # Ngưỡng cho Doji
    
    for idx in df_result.index:
        row = df_result.loc[idx]
        
        # 1. Nến Doji và các biến thể
        if row['body_ratio'] <= DOJI_THRESHOLD:
            # Star
            if (row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and 
                row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and 
                abs(row['lower_shadow_ratio'] - row['upper_shadow_ratio']) <= 0.02):  # Gần bằng nhau
                df_result.loc[idx, 'candle_pattern'] = 'Star Doji'
            # Long Legged Doji    
            elif (abs(row['upper_shadow_ratio'] - row['lower_shadow_ratio']) <= 0.1 and
                  row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
                  row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                df_result.loc[idx, 'candle_pattern'] = 'Long Legged Doji'
            # Dragonfly Doji
            elif (row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
                  row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                df_result.loc[idx, 'candle_pattern'] = 'Dragonfly Doji'
            # Gravestone Doji
            elif (row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
                  row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
                df_result.loc[idx, 'candle_pattern'] = 'Gravestone Doji'
            # Doji thông thường
            else:
                df_result.loc[idx, 'candle_pattern'] = 'Doji'
        
        # 2. Nến Marubozu
        elif (row['body_ratio'] >= LARGE_BODY_THRESHOLD and
              row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD and
              row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD):
            df_result.loc[idx, 'candle_pattern'] = 'Marubozu'
        
        # 3. Nến Spinning Top
        elif (row['body_ratio'] <= SMALL_BODY_THRESHOLD and
              row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
              row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD):
            df_result.loc[idx, 'candle_pattern'] = 'Spinning Top'
        
        # 4. Nến Hammer/Hanging Man (dựa trên xu hướng tuần)
        elif (row['body_ratio'] <= SMALL_BODY_THRESHOLD and
              row['lower_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
              row['upper_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD):
            # Nếu trong xu hướng giảm -> Hammer (tín hiệu đảo chiều tăng)
            if row['weekly_trend'] == 'downtrend':
                df_result.loc[idx, 'candle_pattern'] = 'Hammer'
            # Nếu trong xu hướng tăng -> Hanging Man (tín hiệu đảo chiều giảm)
            elif row['weekly_trend'] == 'uptrend':
                df_result.loc[idx, 'candle_pattern'] = 'Hanging Man'
            # Nếu trong xu hướng ngang -> Hammer (mặc định)
            else:
                df_result.loc[idx, 'candle_pattern'] = 'Hammer'
        
        # 5. Nến Inverted Hammer/Shooting Star (dựa trên xu hướng tuần)
        elif (row['body_ratio'] <= SMALL_BODY_THRESHOLD and
              row['upper_shadow_ratio'] >= LARGE_SHADOW_THRESHOLD and
              row['lower_shadow_ratio'] <= SMALL_SHADOW_THRESHOLD):
            # Nếu trong xu hướng giảm -> Inverted Hammer (tín hiệu đảo chiều tăng)
            if row['weekly_trend'] == 'downtrend':
                df_result.loc[idx, 'candle_pattern'] = 'Inverted Hammer'
            # Nếu trong xu hướng tăng -> Shooting Star (tín hiệu đảo chiều giảm)
            elif row['weekly_trend'] == 'uptrend':
                df_result.loc[idx, 'candle_pattern'] = 'Shooting Star'
            # Nếu trong xu hướng ngang -> Inverted Hammer (mặc định)
            else:
                df_result.loc[idx, 'candle_pattern'] = 'Inverted Hammer'
        
        # 6. Nến Standard (mặc định)
        else:
            df_result.loc[idx, 'candle_pattern'] = 'Standard'
    
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
    
    pattern_counts = df['candle_pattern'].value_counts().to_dict()
    total_candles = len(df)
    
    pattern_percentages = {
        pattern: {
            "count": count,
            "percentage": round((count / total_candles) * 100, 2)
        }
        for pattern, count in pattern_counts.items()
    }
    
    return {
        "total_candles": total_candles,
        "pattern_distribution": pattern_percentages,
        "most_common_pattern": max(pattern_counts, key=pattern_counts.get),
        "pattern_types": list(pattern_counts.keys())
    }

def analyze_candle_patterns(df: pd.DataFrame) -> Dict:
    """
    Phân tích toàn diện các mẫu nến
    
    Args:
        df: DataFrame với OHLC data
        
    Returns:
        Dict chứa phân tích chi tiết
    """
    # Phân loại nến
    df_with_patterns = classify_candle_pattern(df)
    
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
        },
        "detailed_data": df_with_gaps[['Date', 'Open', 'High', 'Low', 'Close', 'candle_pattern', 'gap_type']].to_dict('records')
    }
