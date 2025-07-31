"""
Phân tích tín hiệu từ Moving Averages (MA10, MA50, MA100, MA200)
"""
import pandas as pd
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.moving_averages import calculate_moving_averages


def analyze_ma_signals(df: pd.DataFrame) -> list:
    """
    Phân tích tín hiệu giao dịch từ Moving Averages theo thuật toán:
    - MA nhỏ cắt MA lớn và sau 1 ngày MA_nhỏ - MA_lớn > 0 → BUY (golden cross + confirmation)
    - MA nhỏ cắt MA lớn và sau 1 ngày MA_nhỏ - MA_lớn < 0 → SELL (death cross + confirmation)
    - Volume filter: Volume < average*0.5 → HOLD (tín hiệu nhiễu)
    
    Args:
        df: DataFrame chứa dữ liệu OHLC
    
    Returns:
        List tín hiệu từ MA cross analysis
    """
    ma_signals = []
    
    if df is None or len(df) == 0:
        return ma_signals
    
    # Tính Moving Averages cho DataFrame
    df_with_ma = calculate_moving_averages(df)
    
    if df_with_ma is None or len(df_with_ma) == 0:
        return ma_signals
    
    # Tạo copy của DataFrame để xử lý
    df_processed = df_with_ma.copy()
    
    # Tính toán Average Volume của 20 ngày gần nhất
    if 'Volume_MA20' not in df_processed.columns:
        df_processed['Volume_MA20'] = df_processed['Volume'].rolling(window=20, min_periods=1).mean()
    
    # Chuyển đổi Date nếu cần
    if 'Date' in df_processed.columns and df_processed['Date'].dtype == 'object':
        df_processed['Date'] = pd.to_datetime(df_processed['Date'], format='%d/%m/%Y')
    
    # Các cặp MA để phân tích (MA nhỏ, MA lớn)
    ma_pairs = [
        ('MA10', 'MA50'),
        ('MA10', 'MA100'), 
        ('MA10', 'MA200'),
        ('MA50', 'MA100'),
        ('MA50', 'MA200'),
        ('MA100', 'MA200')
    ]
    
    # Phân tích từng điểm dữ liệu (cần ít nhất 2 điểm để phát hiện cross)
    for i in range(2, len(df_processed)):  # Bắt đầu từ index 2 để có đủ dữ liệu cho cross confirmation
        current_row = df_processed.iloc[i]
        prev_row = df_processed.iloc[i-1]
        prev_prev_row = df_processed.iloc[i-2]
        
        date = current_row.get('Date', f"Position {i}")
        volume_current = current_row.get('Volume', 0)
        volume_avg = current_row.get('Volume_MA20', 0)
        
        # Phân tích từng cặp MA
        for ma_small, ma_large in ma_pairs:
            signal = analyze_ma_cross_signal(
                ma_small_prev2=prev_prev_row.get(ma_small, 0),
                ma_large_prev2=prev_prev_row.get(ma_large, 0),
                ma_small_prev=prev_row.get(ma_small, 0),
                ma_large_prev=prev_row.get(ma_large, 0),
                ma_small_current=current_row.get(ma_small, 0),
                ma_large_current=current_row.get(ma_large, 0),
                volume_current=volume_current,
                volume_avg=volume_avg,
                ma_pair_name=f"{ma_small}/{ma_large}"
            )
            
            # Chỉ thêm tín hiệu nếu không phải HOLD
            if signal['action'] != 'HOLD':
                signal_data = {
                    "date": date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date),
                    "action": signal['action'],
                    "reason": signal['reason'],
                    "ma_pair": f"{ma_small}/{ma_large}",
                    "ma_small_value": round(current_row.get(ma_small, 0), 2),
                    "ma_large_value": round(current_row.get(ma_large, 0), 2),
                    "ma_difference": round(current_row.get(ma_small, 0) - current_row.get(ma_large, 0), 2),
                    "volume_ratio": round(volume_current / volume_avg, 2) if volume_avg > 0 else 0,
                    "signal_type": "ma_cross_analysis"
                }
                ma_signals.append(signal_data)
    
    return ma_signals


def analyze_ma_cross_signal(ma_small_prev2: float, ma_large_prev2: float,
                           ma_small_prev: float, ma_large_prev: float,
                           ma_small_current: float, ma_large_current: float,
                           volume_current: float, volume_avg: float,
                           ma_pair_name: str) -> dict:
    """
    Phân tích tín hiệu MA cross tại một vị trí cụ thể theo thuật toán:
    
    Cross Detection Logic:
    - Phát hiện cross: MA_small đi từ dưới lên trên MA_large hoặc ngược lại
    - Confirmation sau 1 ngày: 
      * Nếu MA_small - MA_large > 0 sau cross → BUY (golden cross confirmed)
      * Nếu MA_small - MA_large < 0 sau cross → SELL (death cross confirmed)
    
    Volume filter:
    - Volume < average*0.5 → HOLD (tín hiệu nhiễu)
    
    Args:
        ma_small_prev2: MA nhỏ 2 ngày trước
        ma_large_prev2: MA lớn 2 ngày trước  
        ma_small_prev: MA nhỏ ngày trước
        ma_large_prev: MA lớn ngày trước
        ma_small_current: MA nhỏ hiện tại
        ma_large_current: MA lớn hiện tại
        volume_current: Volume hiện tại
        volume_avg: Volume trung bình 20 ngày
        ma_pair_name: Tên cặp MA (ví dụ: "MA10/MA50")
    
    Returns:
        Dict chứa action và reason
    """
    
    # Kiểm tra volume trước - nếu thấp thì tất cả là HOLD
    volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1
    
    if volume_ratio < 0.5:  # Volume thấp hơn 50% trung bình
        return {
            "action": "HOLD",
            "reason": f"Very low volume ({volume_ratio:.2f}x avg) - MA cross signal may be unreliable"
        }
    
    # Kiểm tra tính hợp lệ của dữ liệu
    if any(val == 0 or pd.isna(val) for val in [ma_small_prev2, ma_large_prev2, ma_small_prev, ma_large_prev, ma_small_current, ma_large_current]):
        return {
            "action": "HOLD",
            "reason": f"Insufficient MA data for {ma_pair_name} cross analysis"
        }
    
    # === PHÂN TÍCH CROSS VÀ CONFIRMATION ===
    
    # Tính toán các chênh lệch
    diff_prev2 = ma_small_prev2 - ma_large_prev2
    diff_prev = ma_small_prev - ma_large_prev
    diff_current = ma_small_current - ma_large_current
    
    # 1. Phát hiện Golden Cross (MA nhỏ cắt lên trên MA lớn)
    if diff_prev2 <= 0 and diff_prev > 0:  # Cross đã xảy ra ngày hôm trước 
        # Confirmation hôm nay
        if diff_current > 0:  # MA nhỏ vẫn trên MA lớn → xác nhận golden cross
            return {
                "action": "BUY",
                "reason": f"Golden cross confirmed: {ma_pair_name} cross with positive difference ({diff_current:.2f})"
            }
        else:  # MA nhỏ đã quay xuống dưới MA lớn → cross thất bại
            return {
                "action": "HOLD",
                "reason": f"Failed golden cross: {ma_pair_name} cross failed confirmation ({diff_current:.2f})"
            }
    
    # 2. Phát hiện Death Cross (MA nhỏ cắt xuống dưới MA lớn)
    elif diff_prev2 >= 0 and diff_prev < 0:  # Cross đã xảy ra ngày hôm trước
        # Confirmation hôm nay
        if diff_current < 0:  # MA nhỏ vẫn dưới MA lớn → xác nhận death cross
            return {
                "action": "SELL",
                "reason": f"Death cross confirmed: {ma_pair_name} cross with negative difference ({diff_current:.2f})"
            }
        else:  # MA nhỏ đã quay lên trên MA lớn → cross thất bại
            return {
                "action": "HOLD", 
                "reason": f"Failed death cross: {ma_pair_name} cross failed confirmation ({diff_current:.2f})"
            }
    
    # 3. Không có cross hoặc cross chưa được confirm
    else:
        return {
            "action": "HOLD",
            "reason": f"No confirmed MA cross for {ma_pair_name} (diff: {diff_current:.2f})"
        }


# def identify_ma_trend_strength(df: pd.DataFrame, position: int) -> dict:
#     """
#     Xác định độ mạnh của xu hướng dựa trên MA alignment
    
#     Args:
#         df: DataFrame chứa dữ liệu MA
#         position: Vị trí cần phân tích
    
#     Returns:
#         Dict chứa thông tin về độ mạnh xu hướng
#     """
#     if position >= len(df):
#         return {"strength": "unknown", "alignment": "mixed"}
    
#     row = df.iloc[position]
#     ma10 = row.get('MA10', 0)
#     ma50 = row.get('MA50', 0)
#     ma100 = row.get('MA100', 0)  
#     ma200 = row.get('MA200', 0)
    
#     # Kiểm tra tính hợp lệ
#     if any(val == 0 or pd.isna(val) for val in [ma10, ma50, ma100, ma200]):
#         return {"strength": "insufficient_data", "alignment": "incomplete"}
    
#     # Kiểm tra alignment (sắp xếp theo thứ tự)
#     mas = [ma10, ma50, ma100, ma200]
    
#     # Bullish alignment: MA10 > MA50 > MA100 > MA200
#     if all(mas[i] > mas[i+1] for i in range(len(mas)-1)):
#         return {"strength": "strong_bullish", "alignment": "perfect_bullish"}
    
#     # Bearish alignment: MA10 < MA50 < MA100 < MA200  
#     elif all(mas[i] < mas[i+1] for i in range(len(mas)-1)):
#         return {"strength": "strong_bearish", "alignment": "perfect_bearish"}
    
#     # Mixed alignment
#     else:
#         bullish_count = sum(1 for i in range(len(mas)-1) if mas[i] > mas[i+1])
#         bearish_count = sum(1 for i in range(len(mas)-1) if mas[i] < mas[i+1])
        
#         if bullish_count > bearish_count:
#             return {"strength": "weak_bullish", "alignment": "mostly_bullish"}
#         elif bearish_count > bullish_count:
#             return {"strength": "weak_bearish", "alignment": "mostly_bearish"}
#         else:
#             return {"strength": "neutral", "alignment": "mixed"}
