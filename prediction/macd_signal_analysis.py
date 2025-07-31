import pandas as pd
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.macd import calculate_macd


def analyze_macd_position_signal(
    macd_current: float, signal_current: float, histogram_current: float,
    macd_prev: float, signal_prev: float, 
    close_current: float, close_prev: float, close_prev2: float,
    volume_current: float, volume_avg: float
) -> dict:
    """
    Phân tích tín hiệu MACD dựa trên các điều kiện cụ thể theo thuật toán:
    
    THUẬT TOÁN MACD SIGNAL ANALYSIS:
    ================================
    
    1. VOLUME FILTER (Lọc tín hiệu nhiễu):
       - Volume < 0.5 * average → HOLD
       - Lý do: Volume thấp → tín hiệu không đáng tin cậy
    
    2. MACD CROSSOVER ANALYSIS (Phân tích giao cắt):
       - MACD Line cắt lên Signal Line và MACD < 0 → BUY (Bullish crossover)
       - MACD Line cắt xuống Signal Line và MACD > 0 → SELL (Bearish crossover)
       - Lý do: Crossover dưới/trên trục 0 có độ tin cậy cao hơn
    
    3. MACD-PRICE DIVERGENCE ANALYSIS (Phân tích phân kỳ):
       - Bullish Divergence: Giá giảm nhưng MACD tăng → BUY
       - Bearish Divergence: Giá tăng nhưng MACD giảm → SELL
       - Lý do: Phân kỳ báo hiệu sự thay đổi momentum trước khi giá đảo chiều
    
    4. SIDEWAYS/NEUTRAL ZONE (Vùng sideway):
       - |MACD - Signal| < 0.01 và |MACD| < 0.05 → HOLD
       - Lý do: MACD gần Signal Line và gần trục 0 → thị trường sideway
    
    Thứ tự ưu tiên: Volume Filter → Crossover → Divergence → Neutral
    
    Args:
        macd_current: Giá trị MACD hiện tại
        signal_current: Giá trị Signal Line hiện tại  
        histogram_current: Giá trị Histogram hiện tại (MACD - Signal)
        macd_prev: Giá trị MACD ngày trước
        signal_prev: Giá trị Signal Line ngày trước
        close_current: Giá đóng cửa hiện tại
        close_prev: Giá đóng cửa ngày trước
        close_prev2: Giá đóng cửa 2 ngày trước
        volume_current: Volume hiện tại
        volume_avg: Volume trung bình 20 ngày
    
    Returns:
        Dict chứa action (BUY/SELL/HOLD), reason và signal_type
    """
    # Volume filter (< 0.5 * average)
    if pd.notna(volume_avg) and volume_current < 0.5 * volume_avg:
        return {
            'action': 'HOLD',
            'reason': f'Very low volume ({volume_current/volume_avg:.2f}x avg) - MACD signal may be unreliable',
            'signal_type': 'volume_filter'
        }
    
    # 1. MACD Crossover Analysis
    crossover_signal = detect_macd_crossover_signal(
        macd_current, signal_current, macd_prev, signal_prev
    )
    
    if crossover_signal['action'] != 'HOLD':
        return crossover_signal
    
    # 2. MACD Divergence Analysis  
    divergence_signal = analyze_macd_price_divergence(
        macd_current, macd_prev, close_current, close_prev, close_prev2
    )
    
    if divergence_signal['action'] != 'HOLD':
        return divergence_signal
    
    # 3. Sideways/Neutral Zone
    if abs(macd_current - signal_current) < 0.01 and abs(macd_current) < 0.05:
        return {
            'action': 'HOLD',
            'reason': f'MACD near signal line and close to zero axis - sideways movement',
            'signal_type': 'neutral_zone'
        }
    
    return {
        'action': 'HOLD',
        'reason': 'No clear MACD signal detected',
        'signal_type': 'no_signal'
    }


def detect_macd_crossover_signal(macd_current: float, signal_current: float, 
                                macd_prev: float, signal_prev: float) -> dict:
    """
    Phát hiện MACD Line cắt Signal Line
    """
    # Check for crossover
    current_above = macd_current > signal_current
    prev_above = macd_prev > signal_prev
    
    # MACD Line cắt lên Signal Line và dưới trục 0 -> MUA
    if not prev_above and current_above and macd_current < 0:
        return {
            'action': 'BUY',
            'reason': f'MACD line crossed above signal line below zero axis - bullish crossover',
            'signal_type': 'bullish_crossover'
        }
    
    # MACD Line cắt xuống Signal Line và trên trục 0 -> BÁN  
    elif prev_above and not current_above and macd_current > 0:
        return {
            'action': 'SELL',
            'reason': f'MACD line crossed below signal line above zero axis - bearish crossover',
            'signal_type': 'bearish_crossover'
        }
    
    return {
        'action': 'HOLD',
        'reason': 'No significant MACD crossover',
        'signal_type': 'no_crossover'
    }


def analyze_macd_price_divergence(macd_current: float, macd_prev: float,
                                 close_current: float, close_prev: float, close_prev2: float) -> dict:
    """
    Phân tích phân kỳ giữa MACD và giá
    """
    # Phân kỳ dương: giá giảm trong 3 ngày, MACD tăng -> MUA
    
    if close_current < close_prev < close_prev2  and macd_current > macd_prev :
        return {
            'action': 'BUY',
            'reason': f'Bullish divergence - price declining but MACD rising',
            'signal_type': 'bullish_divergence'
        }
    
    # Phân kỳ âm: giá tăng trong 3 ngày, MACD giảm -> BÁN
    if close_current > close_prev > close_prev2 and macd_current < macd_prev :
        return {
            'action': 'SELL',
            'reason': f'Bearish divergence - price rising but MACD declining',
            'signal_type': 'bearish_divergence'
        }
    
    return {
        'action': 'HOLD',
        'reason': 'No significant MACD-price divergence',
        'signal_type': 'no_divergence'
    }


def analyze_macd_signals(df: pd.DataFrame) -> list:
    """
    Phân tích tín hiệu giao dịch từ MACD
    
    Args:
        df: DataFrame chứa dữ liệu OHLC
    
    Returns:
        List tín hiệu từ MACD analysis
    """
    macd_signals = []
    
    if df is None or len(df) <= 2:
        return macd_signals
    
    # Tính MACD cho DataFrame
    df_with_macd = calculate_macd(df)
    
    if df_with_macd is None or len(df_with_macd) <= 2:
        return macd_signals
    
    # Tạo copy của DataFrame để xử lý
    df_processed = df_with_macd.copy()
    
    # Filter volume similar to other algorithms (< 0.5 * average)
    average_volume = df_processed['Volume'].rolling(window=20).mean()
    
    for i in range(2, len(df_processed)):
        current_row = df_processed.iloc[i]
        previous_row = df_processed.iloc[i-1]
        prev2_row = df_processed.iloc[i-2]
        
        date = current_row.get('Date', f'Day_{i}')
        volume_current = current_row['Volume']
        volume_avg = average_volume.iloc[i]
        
        # Skip if volume is too low (< 0.5 * average)
        if pd.notna(volume_avg) and volume_current < 0.5 * volume_avg:
            continue
            
        # Get MACD values
        macd_current = current_row.get('MACD', 0)
        signal_current = current_row.get('MACD_Signal', 0)
        histogram_current = current_row.get('MACD_Histogram', 0)
        
        macd_prev = previous_row.get('MACD', 0)
        signal_prev = previous_row.get('MACD_Signal', 0)
        
        # Skip if MACD data is not available
        if pd.isna(macd_current) or pd.isna(signal_current):
            continue
        
        # Analyze MACD signal
        macd_signal = analyze_macd_position_signal(
            macd_current=macd_current,
            signal_current=signal_current,
            histogram_current=histogram_current,
            macd_prev=macd_prev,
            signal_prev=signal_prev,
            close_current=current_row['Close'],
            close_prev=previous_row['Close'],
            close_prev2=prev2_row['Close'],
            volume_current=volume_current,
            volume_avg=volume_avg
        )
        
        if macd_signal['action'] != 'HOLD':
            macd_signals.append({
                "date": date,
                "action": macd_signal['action'],
                "reason": macd_signal['reason'],
                "macd_value": round(macd_current, 4),
                "signal_line": round(signal_current, 4), 
                "histogram": round(histogram_current, 4),
                "signal_type": macd_signal['signal_type'],
                "close_price": current_row['Close'],
                "volume_ratio": round(volume_current / volume_avg, 2) if pd.notna(volume_avg) else 0
            })
    
    return macd_signals



