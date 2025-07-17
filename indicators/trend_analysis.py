import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

def calculate_weekly_trend(df: pd.DataFrame, symbol: str, start_date: str, end_date: str) -> List[Dict]:
    """Tính xu hướng giá theo tuần dựa trên thay đổi giá đóng cửa"""
    # Sao chép dataframe để không ảnh hưởng đến dữ liệu gốc
    df_temp = df.copy()
    
    # Đảm bảo Date là datetime (có thể đã là datetime rồi)
    if df_temp['Date'].dtype == 'object':
        df_temp['Date'] = pd.to_datetime(df_temp['Date'], format='%d/%m/%Y')
    
    # Sắp xếp theo ngày
    df_temp = df_temp.sort_values('Date')
    
    # Lọc dữ liệu trong khoảng thời gian
    start_dt = pd.to_datetime(start_date).tz_localize(None)
    end_dt = pd.to_datetime(end_date).tz_localize(None)
    
    # Đảm bảo Date column cũng không có timezone
    if df_temp['Date'].dt.tz is not None:
        df_temp['Date'] = df_temp['Date'].dt.tz_localize(None)
    
    df_temp = df_temp[(df_temp['Date'] >= start_dt) & (df_temp['Date'] <= end_dt)]
    
    # Thêm cột week để nhóm theo tuần
    df_temp['Week'] = df_temp['Date'].dt.isocalendar().week
    df_temp['Year'] = df_temp['Date'].dt.year
    df_temp['WeekYear'] = df_temp['Year'].astype(str) + '_' + df_temp['Week'].astype(str)
    
    trends = []
    
    # Nhóm theo tuần
    for week_year, week_data in df_temp.groupby('WeekYear'):
        if len(week_data) < 1:
            continue
        
        # Sắp xếp theo ngày trong tuần
        week_data = week_data.sort_values('Date')
        
        # Format ngày
        start_week = week_data.iloc[0]['Date'].strftime('%d/%m/%Y')
        end_week = week_data.iloc[-1]['Date'].strftime('%d/%m/%Y')
        
        # Lấy giá đóng cửa đầu tuần và cuối tuần
        first_close = week_data.iloc[0]['Close']
        last_close = week_data.iloc[-1]['Close']
        
        # Tính phần trăm thay đổi
        if first_close != 0:
            percent_change = ((last_close - first_close) / first_close) * 100
        else:
            percent_change = 0
        
        # Kiểm tra tuần có ít hơn 3 ngày
        if len(week_data) < 3:
            trends.append({
                "symbol": symbol,
                "period": f"{start_week} to {end_week}",
                "trend": "undefined due to insufficient data (< 3 days)",
                "percent_change": f"{round(percent_change, 2)} %",
                "days_count": len(week_data)
            })
            continue
        
        # Xác định xu hướng
        if percent_change >= 1:
            trend = "uptrend"
        elif percent_change <= -1:
            trend = "downtrend"
        else:
            trend = "sideways trend"
        
        trends.append({
            "symbol": symbol,
            "period": f"{start_week} to {end_week}",
            "trend": trend,
            "percent_change":  f"{round(percent_change, 2)} %",
            "days_count": len(week_data)
        })
    
    return trends

def get_trend_summary(trends: List[Dict]) -> Dict:
    """
    Tạo tóm tắt xu hướng
    
    Args:
        trends: List các xu hướng tuần (bao gồm cả những tuần bị bỏ qua)
    
    Returns:
        Dict chứa thống kê xu hướng
    """
    if not trends:
        return {
            "total_weeks": 0,
            "uptrend_weeks": 0,
            "downtrend_weeks": 0,
            "sideways_weeks": 0,
            "insufficient_data_weeks": 0,
            "dominant_trend": "unknown"
        }
    
    uptrend_count = sum(1 for t in trends if t["trend"] == "uptrend")
    downtrend_count = sum(1 for t in trends if t["trend"] == "downtrend")
    sideways_count = sum(1 for t in trends if t["trend"] == "sideways trend")
    insufficient_count = sum(1 for t in trends if t["trend"] == "insufficient data (< 3 days)")
    
    # Xác định xu hướng chủ đạo (chỉ tính các tuần có dữ liệu đủ)
    valid_trends = [uptrend_count, downtrend_count, sideways_count]
    max_count = max(valid_trends)
    
    if max_count == 0:
        dominant_trend = "insufficient data"
    elif uptrend_count == max_count:
        dominant_trend = "uptrend"
    elif downtrend_count == max_count:
        dominant_trend = "downtrend"
    else:
        dominant_trend = "sideways trend"
    
    return {
        "total_weeks": len(trends),
        "uptrend_weeks": uptrend_count,
        "downtrend_weeks": downtrend_count,
        "sideways_weeks": sideways_count,
        "insufficient_data_weeks": insufficient_count,
        "dominant_trend": dominant_trend
    }
