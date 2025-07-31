"""
Phân tích tín hiệu từ RSI (Relative Strength Index)
"""
import pandas as pd
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.rsi import calculate_rsi


def analyze_rsi_signals(df: pd.DataFrame) -> list:
    """
    Phân tích tín hiệu giao dịch từ RSI theo thuật toán mới:
    - RSI >= 70: Overbought zone → SELL signal 
    - RSI <= 30: Oversold zone → BUY signal
    - RSI >= 90: Extreme overbought (reversal expectation) → BUY signal (đảo chiều từ SELL)
    - RSI <= 10: Extreme oversold (reversal expectation) → SELL signal (đảo chiều từ BUY)
    - Kết hợp với volume analysis để xác nhận tín hiệu
    
    Args:
        df: DataFrame chứa dữ liệu OHLC
    
    Returns:
        List tín hiệu từ RSI analysis
    """
    rsi_signals = []
    
    if df is None or len(df) == 0:
        return rsi_signals
    
    # Tính RSI cho DataFrame
    df_with_rsi = calculate_rsi(df)
    
    if df_with_rsi is None or len(df_with_rsi) == 0:
        return rsi_signals
    
    # Tạo copy của DataFrame để xử lý  
    df_processed = df_with_rsi.copy()
    
    # Tính toán Average Volume của 20 ngày gần nhất
    df_processed['Volume_MA20'] = df_processed['Volume'].rolling(window=20, min_periods=1).mean()
    
    # Chuyển đổi Date nếu cần
    if 'Date' in df_processed.columns and df_processed['Date'].dtype == 'object':
        df_processed['Date'] = pd.to_datetime(df_processed['Date'], format='%d/%m/%Y')
    
    # Phân tích từng điểm dữ liệu
    for i in range(1, len(df_processed)):  # Bắt đầu từ index 1 để so sánh với điểm trước
        current_row = df_processed.iloc[i]
        prev_row = df_processed.iloc[i-1]
        
        date = current_row.get('Date', f"Position {i}")
        rsi_current = current_row.get('RSI', 50)
        rsi_prev = prev_row.get('RSI', 50)
        volume_current = current_row.get('Volume', 0)
        volume_avg = current_row.get('Volume_MA20', 0)
        
        # Phân tích tín hiệu RSI với mức cố định
        signal = analyze_rsi_position_signal(
            rsi_current, rsi_prev, 
            volume_current, volume_avg
        )
        
        # Chỉ thêm tín hiệu nếu không phải HOLD
        if signal['action'] != 'HOLD':
            signal_data = {
                "date": date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else str(date),
                "action": signal['action'],
                "reason": signal['reason'],
                "rsi_value": round(rsi_current, 2),
                "volume_ratio": round(volume_current / volume_avg, 2) if volume_avg > 0 else 0,
                "signal_type": "rsi_analysis"
            }
            rsi_signals.append(signal_data)
    
    return rsi_signals


def analyze_rsi_position_signal(rsi_current: float, rsi_prev: float, 
                               volume_current: float, volume_avg: float) -> dict:
    """
    Phân tích tín hiệu RSI tại một vị trí cụ thể theo thuật toán reversal expectation:
    
    Fixed RSI Levels với Reversal Logic:
    - RSI >= 70: Overbought zone → SELL signal
    - RSI <= 30: Oversold zone → BUY signal
    - RSI >= 90: Extreme overbought (reversal expectation) → BUY signal (đảo chiều từ SELL)
    - RSI <= 10: Extreme oversold (reversal expectation) → SELL signal (đảo chiều từ BUY)
    
    Volume filter:
    - Volume < average*0.5 → chuyển tất cả thành HOLD (tín hiệu nhiễu)
    
    Args:
        rsi_current: RSI hiện tại
        rsi_prev: RSI trước đó
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
            "reason": f"Very low volume ({volume_ratio:.2f}x avg) - RSI signal may be unreliable"
        }
    
    # === PHÂN TÍCH TÍN HIỆU RSI VỚI REVERSAL EXPECTATION ===
    
    # 1. Kiểm tra Extreme levels (10/90) - Reversal Expectation Signals
    if rsi_current >= 90 and rsi_prev < 90:  # Vừa chạm extreme overbought - đảo chiều từ SELL thành BUY
        return {
            "action": "BUY",
            "reason": f"RSI hit extreme overbought ({rsi_current:.1f}) ≥ 90 - reversal expectation signal (flip from SELL to BUY)"
        }
    
    elif rsi_current <= 10 and rsi_prev > 10:  # Vừa chạm extreme oversold - đảo chiều từ BUY thành SELL
        return {
            "action": "SELL",
            "reason": f"RSI hit extreme oversold ({rsi_current:.1f}) ≤ 10 - reversal expectation signal (flip from BUY to SELL)"
        }
    
    # 2. Kiểm tra Standard levels (30/70) - Oversold/Overbought Signals (chỉ khi chưa chạm extreme)
    elif rsi_current >= 70 and rsi_current < 90 and rsi_prev < 70:  # Vào overbought nhưng chưa chạm extreme
        return {
            "action": "SELL",
            "reason": f"RSI entered overbought zone ({rsi_current:.1f}) ≥ 70 - sell signal"
        }
    
    elif rsi_current <= 30 and rsi_current > 10 and rsi_prev > 30:  # Vào oversold nhưng chưa chạm extreme
        return {
            "action": "BUY",
            "reason": f"RSI entered oversold zone ({rsi_current:.1f}) ≤ 30 - buy signal"
        }
    
    # 2.1 Kiểm tra giảm sâu trong vùng oversold hoặc tăng cao trong vùng overbought
    elif rsi_current <= 25 and rsi_current > 10 and rsi_prev <= 30 and rsi_prev > rsi_current:  # Tiếp tục giảm sâu trong vùng oversold
        return {
            "action": "BUY",
            "reason": f"RSI deepening in oversold zone ({rsi_current:.1f}) ≤ 25 - strong buy signal"
        }
    
    elif rsi_current >= 75 and rsi_current < 90 and rsi_prev >= 70 and rsi_prev < rsi_current:  # Tiếp tục tăng cao trong vùng overbought
        return {
            "action": "SELL",
            "reason": f"RSI rising in overbought zone ({rsi_current:.1f}) ≥ 75 - strong sell signal"
        }
    # 3. Kiểm tra exit signals - thoát khỏi extreme zones
    elif rsi_prev <= 10 and rsi_current > 10:  # Thoát khỏi extreme oversold
        return {
            "action": "HOLD",
            "reason": f"RSI exited extreme oversold zone ({rsi_current:.1f}) - wait for confirmation"
        }
    
    elif rsi_prev >= 90 and rsi_current < 90:  # Thoát khỏi extreme overbought
        return {
            "action": "HOLD",
            "reason": f"RSI exited extreme overbought zone ({rsi_current:.1f}) - wait for confirmation"
        }
    
    # 4. Không có tín hiệu đặc biệt
    else:
        return {
            "action": "HOLD",
            "reason": f"RSI at {rsi_current:.1f} - no significant level break (30/70 oversold/overbought, 10/90 extreme)"
        }
