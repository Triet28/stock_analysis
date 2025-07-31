"""
Phân tích tín hiệu từ Bollinger Bands
"""
import pandas as pd
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.bollinger_bands import calculate_bollinger_bands


def analyze_bb_signals(df: pd.DataFrame) -> list:
    """
    Phân tích tín hiệu giao dịch từ Bollinger Bands theo thuật toán:
    - Giá close chạm/cắt xuống dải dưới → BUY
    - Giá close chạm/cắt lên dải trên → SELL
    - Volume filter: Volume < average*0.5 → HOLD (tín hiệu nhiễu)
    
    Args:
        df: DataFrame chứa dữ liệu OHLC
    
    Returns:
        List tín hiệu từ Bollinger Bands analysis
    """
    bb_signals = []
    
    if df is None or len(df) == 0:
        return bb_signals
    
    # Tính Bollinger Bands cho DataFrame
    df_with_bb = calculate_bollinger_bands(df)
    
    if df_with_bb is None or len(df_with_bb) == 0:
        return bb_signals
    
    # Tạo copy của DataFrame để xử lý
    df_processed = df_with_bb.copy()
    
    # Tính toán Average Volume của 20 ngày gần nhất
    if 'Volume_MA20' not in df_processed.columns:
        df_processed['Volume_MA20'] = df_processed['Volume'].rolling(window=20, min_periods=1).mean()
    
    # Chuyển đổi Date nếu cần
    if 'Date' in df_processed.columns and df_processed['Date'].dtype == 'object':
        df_processed['Date'] = pd.to_datetime(df_processed['Date'], format='%d/%m/%Y')
    
    # Phân tích từng điểm dữ liệu (cần ít nhất 1 điểm trước để so sánh)
    for i in range(1, len(df_processed)):
        current_row = df_processed.iloc[i]
        prev_row = df_processed.iloc[i-1]
        
        date = current_row.get('Date', f"Position {i}")
        close_current = current_row.get('Close', 0)
        close_prev = prev_row.get('Close', 0)
        bb_upper_current = current_row.get('BB_Upper', 0)
        bb_lower_current = current_row.get('BB_Lower', 0)
        bb_middle_current = current_row.get('BB_Middle', 0)
        volume_current = current_row.get('Volume', 0)
        volume_avg = current_row.get('Volume_MA20', 0)
        
        # Phân tích tín hiệu Bollinger Bands
        signal = analyze_bb_position_signal(
            close_current=close_current,
            close_prev=close_prev,
            bb_upper=bb_upper_current,
            bb_lower=bb_lower_current,
            bb_middle=bb_middle_current,
            volume_current=volume_current,
            volume_avg=volume_avg
        )
        
        # Chỉ thêm tín hiệu nếu không phải HOLD
        if signal['action'] != 'HOLD':
            signal_data = {
                "date": date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date),
                "action": signal['action'],
                "reason": signal['reason'],
                "close_price": round(close_current, 2),
                "bb_upper": round(bb_upper_current, 2),
                "bb_lower": round(bb_lower_current, 2),
                "bb_middle": round(bb_middle_current, 2),
                "bb_position": signal.get('bb_position', 0),
                "volume_ratio": round(volume_current / volume_avg, 2) if volume_avg > 0 else 0,
                "signal_type": "bb_analysis"
            }
            bb_signals.append(signal_data)
    
    return bb_signals


def analyze_bb_position_signal(close_current: float, close_prev: float,
                              bb_upper: float, bb_lower: float, bb_middle: float,
                              volume_current: float, volume_avg: float) -> dict:
    """
    Phân tích tín hiệu Bollinger Bands theo thuật toán đơn giản:
    
    - Giá đóng cửa < Lower Band → BUY
    - Giá đóng cửa > Upper Band → SELL  
    - Volume filter: Volume < average*0.5 → HOLD (tín hiệu nhiễu)
    
    Args:
        close_current: Giá close hiện tại
        close_prev: Giá close trước đó (không sử dụng)
        bb_upper: Bollinger Band dải trên
        bb_lower: Bollinger Band dải dưới
        bb_middle: Bollinger Band dải giữa (không sử dụng)
        volume_current: Volume hiện tại
        volume_avg: Volume trung bình 20 ngày
    
    Returns:
        Dict chứa action và reason
    """
    
    # Kiểm tra volume trước - nếu thấp thì tất cả là HOLD
    volume_ratio = volume_current / volume_avg if volume_avg > 0 else 1
    
    if volume_ratio < 0.5:  # Volume thấp hơn 50% trung bình
        return {
            "action": "HOLD",
            "reason": f"Very low volume ({volume_ratio:.2f}x avg) - BB signal may be unreliable"
        }
    
    # Kiểm tra tính hợp lệ của dữ liệu
    if any(val == 0 or pd.isna(val) for val in [close_current, bb_upper, bb_lower]):
        return {
            "action": "HOLD",
            "reason": "Insufficient Bollinger Bands data for analysis"
        }
    
    # Tính toán vị trí trong dải BB (0 = lower band, 1 = upper band)
    if bb_upper == bb_lower:
        bb_position = 0.5
    else:
        bb_position = (close_current - bb_lower) / (bb_upper - bb_lower)

    # === PHÂN TÍCH TÍN HIỆU BOLLINGER BANDS ===
    # 1. Giá đóng cửa < Lower Band → MUA
    if close_current < bb_lower:
        return {
            "action": "BUY",
            "reason": f"Close price ({close_current:.2f}) below lower BB ({bb_lower:.2f}) - buy signal",
            "bb_position": bb_position
        }
    
    # 2. Giá đóng cửa > Upper Band → BÁN
    elif close_current > bb_upper:
        return {
            "action": "SELL",
            "reason": f"Close price ({close_current:.2f}) above upper BB ({bb_upper:.2f}) - sell signal",
            "bb_position": bb_position
        }
    
    # 3. Giá trong khoảng giữa → HOLD
    else:
        return {
            "action": "HOLD",
            "reason": f"Close price ({close_current:.2f}) between BB bands ({bb_lower:.2f} - {bb_upper:.2f})",
            "bb_position": bb_position
        }
