import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

def calculate_trend(df: pd.DataFrame, symbol: str, start_date: str, end_date: str, exchange: str = "Unknown") -> List[Dict]:
    """Tính xu hướng giá theo chu kỳ 15 ngày dựa trên thay đổi giá đóng cửa và exchange"""
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
    
    if len(df_temp) == 0:
        return []
    
    # Thiết lập ngưỡng trend theo exchange
    exchange_upper = exchange.upper()
    
    if exchange_upper == "HSX" or exchange_upper == "HOSE":
        up_threshold = 10
        down_threshold = -10
    elif exchange_upper == "HNX":
        up_threshold = 15
        down_threshold = -15
    elif exchange_upper == "UPCOM":
        up_threshold = 20
        down_threshold = -20
    else:
        raise ValueError(f"Exchange '{exchange}' không được hỗ trợ. Chỉ hỗ trợ: HSX, HOSE, HNX, UPCOM")
    
    trends = []
    start_index = 0
    
    while start_index <= len(df_temp) - 7:  # Đảm bảo còn ít nhất 7 ngày
        # Bắt đầu với window tối đa 15 ngày
        max_end = min(start_index + 15, len(df_temp))
        trend_found = False
        
        # Thử từ window 15 ngày xuống đến 7 ngày
        for current_end in range(max_end, start_index + 6, -1):  # Từ max_end xuống start_index + 7
            window_size = current_end - start_index
            
            # Kiểm tra điều kiện tối thiểu 7 ngày
            if window_size < 7:
                break
                
            period_data = df_temp.iloc[start_index:current_end]
            
            # Format ngày
            start_period = period_data.iloc[0]['Date'].strftime('%d/%m/%Y')
            end_period = period_data.iloc[-1]['Date'].strftime('%d/%m/%Y')
            
            # Lấy giá đóng cửa đầu và cuối chu kỳ
            first_close = period_data.iloc[0]['Close']
            last_close = period_data.iloc[-1]['Close']
            
            # Tính phần trăm thay đổi
            percent_change = ((last_close - first_close) / first_close) * 100

            # Xác định xu hướng
            if percent_change >= up_threshold:
                trend = "uptrend"
                trend_found = True
                
                trends.append({
                    "symbol": symbol,
                    "exchange": exchange,
                    "period": f"{start_period} to {end_period}",
                    "trend": trend,
                    "percent_change": f"{round(percent_change, 2)} %",
                    "days_count": len(period_data)
                })
                
                # Nhảy đến sau chu kỳ vừa tìm thấy
                start_index = current_end
                break
                
            elif percent_change <= down_threshold:
                trend = "downtrend"
                trend_found = True
                
                trends.append({
                    "symbol": symbol,
                    "exchange": exchange,
                    "period": f"{start_period} to {end_period}",
                    "trend": trend,
                    "percent_change": f"{round(percent_change, 2)} %",
                    "days_count": len(period_data)
                })
                
                # Nhảy đến sau chu kỳ vừa tìm thấy
                start_index = current_end
                break
        
        # Nếu không tìm thấy trend nào trong tất cả các window size
        if not trend_found:
            # Dịch chuyển start 1 ngày
            start_index += 1
    
    return trends

def get_trend_summary(trends: List[Dict]) -> Dict:
    """Tạo tóm tắt xu hướng"""
    if not trends:
        return {
            "total_periods": 0,
            "uptrend_periods": 0,
            "downtrend_periods": 0,
            "dominant_trend": None
        }
    
    uptrend_count = sum(1 for t in trends if t["trend"] == "uptrend")
    downtrend_count = sum(1 for t in trends if t["trend"] == "downtrend")
    
    # Xác định xu hướng chủ đạo
    if uptrend_count > downtrend_count:
        dominant_trend = "uptrend"
    elif downtrend_count > uptrend_count:
        dominant_trend = "downtrend"
    else:
        dominant_trend = "balanced"  # Cân bằng giữa up và down
    
    return {
        "total_periods": len(trends),
        "uptrend_periods": uptrend_count,
        "downtrend_periods": downtrend_count,
        "dominant_trend": dominant_trend
    }
