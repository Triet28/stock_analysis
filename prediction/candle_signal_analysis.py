"""
Phân tích tín hiệu từ Candlestick Patterns
"""
import pandas as pd
import sys
import os

# Thêm parent directory vào path để import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from indicators.candle_patterns import classify_candle_pattern


def analyze_candle_signals(df: pd.DataFrame, trends: list, exchange: str) -> list:
    """
    Phân tích tín hiệu giao dịch từ các pattern nến
    
    Args:
        df: DataFrame chứa dữ liệu OHLC
        trends: Danh sách xu hướng
        exchange: Sàn giao dịch để xác định ngưỡng Marubozu (HSX/HNX/UPCOM)
    
    Returns:
        List tín hiệu từ candle patterns
    """
    candle_signals = []
    
    if df is None or len(df) == 0:
        return candle_signals
    
    # Gọi classify_candle_pattern trực tiếp để phân tích patterns với exchange
    df_with_patterns = classify_candle_pattern(df, exchange, trends)
    
    if df_with_patterns is None or len(df_with_patterns) == 0:
        return candle_signals
    
    # Chuyển đổi DataFrame để dễ xử lý
    df_processed = df_with_patterns.copy()
    if 'Date' in df_processed.columns and df_processed['Date'].dtype == 'object':
        df_processed['Date'] = pd.to_datetime(df_processed['Date'], format='%d/%m/%Y')
    
    # Nhóm các tín hiệu theo trend period để tổng hợp strength
    trend_signals = {}
    
    # Phân tích từng vị trí trong DataFrame
    for i, row in df_processed.iterrows():
        position_date = row.get('Date', f"Position {i}")
        pattern = row.get('candle_pattern', 'Standard')
        close_price = row.get('Close', 0)
        # Lấy trend trực tiếp từ trường trend_context đã được phân loại
        current_trend = row.get('trend_context', None)
        trend_period = None
        # Nếu có danh sách trends, xác định period cho thống kê
        if trends and current_trend:
            for trend in trends:
                trend_start = pd.to_datetime(trend['period'].split(' to ')[0], format='%d/%m/%Y')
                trend_end = pd.to_datetime(trend['period'].split(' to ')[1], format='%d/%m/%Y')
                if isinstance(position_date, str):
                    pos_date = pd.to_datetime(position_date, format='%d/%m/%Y')
                else:
                    pos_date = position_date
                if trend_start <= pos_date <= trend_end:
                    trend_period = trend['period']
                    break
        # Phân tích tín hiệu tại vị trí này
        signal = analyze_position_signal(pattern, current_trend, row, i, df_processed)
        
        # Chỉ xét các pattern đặc biệt và các Doji đặc biệt
        special_patterns = ['Hammer', 'Inverted Hammer', 'Hanging Man', 'Shooting Star',
                          'Star Doji', 'Long Legged Doji', 'Dragonfly Doji', 'Gravestone Doji', 'Marubozu']
        
        # Chỉ thêm vào kết quả nếu pattern đặc biệt VÀ có trend rõ ràng (trừ Marubozu)
        if pattern in special_patterns and (current_trend is not None or pattern == 'Marubozu'):
            signal_data = {
                "date": position_date.strftime('%d/%m/%Y') if hasattr(position_date, 'strftime') else str(position_date),
                "pattern": pattern,
                "trend": current_trend,
                "action": signal['action'],
                "reason": signal['reason'],
                "strength": signal['strength'],
                "price": close_price
            }
            
            # Nhóm theo trend period để tổng hợp
            if trend_period:
                if trend_period not in trend_signals:
                    trend_signals[trend_period] = {
                        'trend': current_trend,
                        'signals': [],
                        'total_strength': 0
                    }
                trend_signals[trend_period]['signals'].append(signal_data)
                trend_signals[trend_period]['total_strength'] += signal['strength']
            else:
                # Marubozu không cần trend - thêm trực tiếp
                candle_signals.append(signal_data)
    
    # Tổng hợp tín hiệu cho từng trend period
    for period, trend_data in trend_signals.items():
        total_strength = trend_data['total_strength']
        signals = trend_data['signals']
        trend_type = trend_data['trend']
        
        # Xác định tín hiệu tổng hợp
        if total_strength > 0:
            combined_action = "BUY"
        elif total_strength < 0:
            combined_action = "SELL"
        else:
            combined_action = "HOLD"
        
        # Thêm tín hiệu tổng hợp cho trend period này
        if signals:  # Nếu có tín hiệu trong period này
            # Tạo danh sách pattern với trend context và chi tiết
            pattern_list = []
            for signal in signals:
                # Xử lý đặc biệt cho Marubozu để hiển thị Green/Red
                if signal['pattern'] == 'Marubozu':
                    # Xác định loại Marubozu từ action
                    marubozu_type = "Green Marubozu" if signal['action'] == 'BUY' else "Red Marubozu"
                    pattern_with_trend = f"{marubozu_type}"
                else:
                    # Các pattern khác giữ nguyên
                    pattern_with_trend = f"{signal['pattern']}"
                    if signal['trend']:
                        pattern_with_trend += f" in {signal['trend']}"
                pattern_list.append(pattern_with_trend)
            
            # Tạo combined pattern string
            combined_pattern = ", ".join(pattern_list)
            
            # Tạo combined reason với strength chi tiết cho từng signal
            reason_parts = []
            for signal in signals[:3]:  # Giới hạn 3 signals đầu
                reason_with_strength = f"{signal['reason']} (strength = {signal['strength']})"
                reason_parts.append(reason_with_strength)
            
            combined_reason = f"Signals in {trend_type} (strength: {total_strength}): " + "; ".join(reason_parts)
            
            candle_signals.append({
                "date": f"{period}",
                "pattern": combined_pattern,
                "trend": trend_type,
                "action": combined_action,
                "reason": combined_reason,
                "strength": total_strength,
                "price": signals[-1]['price'],  # Giá của tín hiệu cuối cùng
                "individual_signals": len(signals)
            })
    
    # Sắp xếp tất cả signal positions theo thời gian
    def parse_date_for_sorting(date_str):
        """Parse date string để sắp xếp, xử lý cả single date và period"""
        if ' to ' in date_str:
            # Với period, lấy ngày bắt đầu để sắp xếp
            start_date = date_str.split(' to ')[0]
            return pd.to_datetime(start_date, format='%d/%m/%Y')
        else:
            # Single date
            return pd.to_datetime(date_str, format='%d/%m/%Y')
    
    # Sắp xếp candle_signals theo thời gian
    candle_signals.sort(key=lambda x: parse_date_for_sorting(x["date"]))
    
    return candle_signals


def analyze_position_signal(pattern: str, trend: str, row: pd.Series, position: int, df: pd.DataFrame) -> dict:
    """
    Phân tích tín hiệu giao dịch cho một vị trí cụ thể
    
    Args:
        pattern: Loại pattern nến
        trend: Xu hướng hiện tại (uptrend/downtrend)
        row: Dữ liệu nến hiện tại
        position: Vị trí trong DataFrame
        df: DataFrame đầy đủ
    
    Returns:
        Dict chứa action, reason, strength
    """
    
    if pattern == 'Standard':
        return {
            "action": "HOLD",
            "reason": "Standard candle - no special signal",
            "strength": 0
        }
    
    # === REVERSAL PATTERNS ===
    if pattern == 'Hammer':
        if trend == 'downtrend':
            # Hammer in downtrend = bullish reversal
            return {
                "action": "BUY",
                "reason": "Hammer pattern in downtrend suggests bullish reversal",
                "strength": 3
            }
        else:
            return {"action": "HOLD", "reason": "Hammer needs downtrend for reversal signal", "strength": 0}
    
    elif pattern == 'Inverted Hammer':
            if trend == 'downtrend':
            # Inverted Hammer in downtrend = potential bullish reversal (weaker than Hammer)
                return {
                    "action": "BUY",
                    "reason": "Inverted Hammer in downtrend suggests potential bullish reversal",
                    "strength": 2
                }
            else: return {
                "action": "HOLD",
                "reason": "Inverted Hammer needs downtrend for reversal signal",
                "strength": 0
            }
    elif pattern == 'Hanging Man':
            # Hanging Man in uptrend = bearish reversal
            return {
                "action": "SELL",
                "reason": "Hanging Man pattern in uptrend suggests bearish reversal",
                "strength": -3
            }
    
    elif pattern == 'Shooting Star':
            # Shooting Star in uptrend = bearish reversal
            return {
                "action": "SELL",
                "reason": "Shooting Star pattern in uptrend suggests bearish reversal",
                "strength": -3
            }
    
    # === DOJI PATTERNS ===
    elif pattern == 'Star Doji':
        # Star Doji cần xác nhận với nến tiếp theo
        confirmation = check_star_doji_confirmation(position, df, trend)
        if confirmation['confirmed']:
            return {
                "action": confirmation['action'],
                "reason": f"Star Doji with confirmation: {confirmation['reason']}",
                "strength": confirmation['strength']
            }
        else:
            return {"action": "HOLD", "reason": "Star Doji needs confirmation from next candle", "strength": 0}
    
    elif pattern == 'Long Legged Doji':
        if trend == 'uptrend':
            return {
                "action": "SELL",
                "reason": "Long Legged Doji in uptrend suggests potential reversal to downside",
                "strength": -2
            }
        elif trend == 'downtrend':
            return {
                "action": "BUY", 
                "reason": "Long Legged Doji in downtrend suggests potential reversal to upside",
                "strength": 2
            }
        else:
            return {"action": "HOLD", 
                    "reason": "Long Legged Doji needs clear trend for reversal signal", 
                    "strength": 0}
    
    elif pattern == 'Dragonfly Doji':
            return {
                "action": "BUY",
                "reason": "Dragonfly Doji in downtrend suggests bullish reversal",
                "strength": 3
            }
    
    elif pattern == 'Gravestone Doji':
            return {
                "action": "SELL",
                "reason": "Gravestone Doji in uptrend suggests bearish reversal",
                "strength": -3
            }
    
    # === CONTINUATION PATTERNS ===
    elif pattern == 'Marubozu':
        # Marubozu không phụ thuộc vào trend - chỉ dựa vào body color
        open_price = row.get('Open', 0)
        close_price = row.get('Close', 0)
        
        # Kiểm tra body movement threshold 15%
        body_movement = abs((close_price - open_price) / open_price) * 100
        if close_price > open_price:
            # Green Marubozu = Bullish
            return {
                "action": "BUY",
                "reason": f"Green Marubozu with {body_movement:.1f}% bullish movement",
                "strength": 4
            }
        else:
            # Red Marubozu = Bearish
            return {
                "action": "SELL",
                "reason": f"Red Marubozu with {body_movement:.1f}% bearish movement",
                "strength": -4
            }
    
    # Default case
    return {
        "action": "HOLD",
        "reason": f"Unknown pattern: {pattern}",
        "strength": 0
    }


def check_star_doji_confirmation(position: int, df: pd.DataFrame, trend: str) -> dict:
    """
    Kiểm tra confirmation cho Star Doji pattern với nến tiếp theo
    
    Args:
        position: Vị trí của Star Doji trong DataFrame
        df: DataFrame chứa dữ liệu
        trend: Xu hướng hiện tại
    
    Returns:
        Dict chứa thông tin confirmation
    """
    
    # Nếu không có nến tiếp theo để confirm
    if position >= len(df) - 1:
        return {
            "confirmed": False,
            "action": "HOLD",
            "reason": "No next candle for confirmation",
            "strength": 0
        }
    
    # Lấy nến hiện tại (Star Doji) và nến tiếp theo
    current_candle = df.iloc[position]
    next_candle = df.iloc[position + 1]
    
    current_close = current_candle.get('Close', 0)
    next_open = next_candle.get('Open', 0)
    next_close = next_candle.get('Close', 0)
    
    # Kiểm tra direction của nến confirmation
    next_is_bullish = next_close > next_open
    next_is_bearish = next_close < next_open
    
    # Logic confirmation dựa trên trend
    if trend == 'uptrend':
        # Trong uptrend, Star Doji + bearish confirmation = reversal signal
        if next_is_bearish:
            return {
                "confirmed": True,
                "action": "SELL",
                "reason": "Star Doji in uptrend confirmed by bearish candle",
                "strength": -3
            }
        else:
            return {
                "confirmed": False,
                "action": "HOLD", 
                "reason": "Star Doji in uptrend but no bearish confirmation",
                "strength": 0
            }
    
    elif trend == 'downtrend':
        # Trong downtrend, Star Doji + bullish confirmation = reversal signal
        if next_is_bullish:
            return {
                "confirmed": True,
                "action": "BUY",
                "reason": "Star Doji in downtrend confirmed by bullish candle",
                "strength": 3
            }
        else:
            return {
                "confirmed": False,
                "action": "HOLD",
                "reason": "Star Doji in downtrend but no bullish confirmation", 
                "strength": 0
            }
    
    else:
        # Không có trend rõ ràng
        return {
            "confirmed": False,
            "action": "HOLD",
            "reason": "Star Doji needs clear trend for confirmation",
            "strength": 0
        }
