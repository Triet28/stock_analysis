from typing import List, Dict
import pandas as pd
from .candle_signal_analysis import analyze_candle_signals
from .rsi_signal_analysis import analyze_rsi_signals
from .ma_signal_analysis import analyze_ma_signals
from .macd_signal_analysis import analyze_macd_signals
from .bb_signal_analysis import analyze_bb_signals


def calculate_statement(signals):
    """Tính statement cho tất cả các phương pháp dựa trên số lượng BUY vs SELL"""
    if not signals:
        return "HOLD"
    buy_count = sum(1 for signal in signals if signal.get('action') == 'BUY')
    sell_count = sum(1 for signal in signals if signal.get('action') == 'SELL')
    if buy_count > sell_count:
        return "BUY"
    elif sell_count > buy_count:
        return "SELL"
    else:
        return "HOLD"

def format_analysis_result(signals, method_name):
    """Format kết quả analysis theo format yêu cầu"""
    if not signals:
        return {
            "analysis": [],
            "statement": "HOLD"
        }
    
    formatted_signals = []
    for signal in signals:
        formatted_signal = {
            "signal": signal.get('action', 'HOLD'),
            "reason": signal.get('reason', 'No reason provided'),
            "date": signal.get('date', 'Unknown date')
        }
        
        # Chỉ candle mới có strength
        if method_name == "Candle":
            formatted_signal["strength"] = signal.get('strength', 0)
            
        formatted_signals.append(formatted_signal)
    
    # Tính statement cho tất cả các phương pháp
    statement = calculate_statement(signals)
    
    return {
        "analysis": formatted_signals,
        "statement": statement
    }

def predict_future_trend(df: pd.DataFrame, trends: list, exchange: str = "HSX") -> dict:
    """
    Dự đoán xu hướng tương lai dựa trên phân tích tổng hợp 5 phương pháp
    
    Args:
        df: DataFrame chứa dữ liệu OHLC gốc
        trends: Danh sách các xu hướng đã phát hiện
        exchange: Sàn giao dịch để xác định ngưỡng Marubozu (HSX/HNX/UPCOM)
    
    Returns:
        Dict chứa tín hiệu giao dịch tổng hợp với final_statement và analysis
    """
    
    if df is None or len(df) == 0:
        return {
            "final_statement": "HOLD",
            "analysis": {
                "RSI": [],
                "Candle": [],
                "MA": [],
                "MACD": [],
                "BB": []
            }
        }
    
    # 1. Phân tích tín hiệu từ RSI (tự gọi calculate_rsi)
    rsi_signals = analyze_rsi_signals(df)
    
    # 2. Phân tích tín hiệu từ Candle Patterns (tự gọi analyze_candle_patterns với exchange)
    candle_signals = analyze_candle_signals(df, trends, exchange)
    
    # 3. Phân tích tín hiệu từ Moving Averages (tự gọi calculate_moving_averages)
    ma_signals = analyze_ma_signals(df)
    
    # 4. Phân tích tín hiệu từ MACD (tự gọi calculate_macd)
    macd_signals = analyze_macd_signals(df)
    
    # 5. Phân tích tín hiệu từ Bollinger Bands (tự gọi calculate_bollinger_bands)
    bb_signals = analyze_bb_signals(df)
    
    # Format kết quả analysis theo yêu cầu
    rsi_analysis = format_analysis_result(rsi_signals, "RSI")
    candle_analysis = format_analysis_result(candle_signals, "Candle") 
    ma_analysis = format_analysis_result(ma_signals, "MA")
    macd_analysis = format_analysis_result(macd_signals, "MACD")
    bb_analysis = format_analysis_result(bb_signals, "BB")
    
    # Tổng hợp tất cả signals để đưa ra quyết định cuối cùng
    all_statements = [
        rsi_analysis["statement"],
        candle_analysis["statement"], 
        ma_analysis["statement"],
        macd_analysis["statement"],
        bb_analysis["statement"]
    ]
    
    # Đếm statements
    buy_count = all_statements.count('BUY')
    sell_count = all_statements.count('SELL')
    
    # Quyết định cuối cùng: >= 3 statements cùng loại
    if buy_count >= 3 and buy_count > sell_count:
        final_statement = "BUY"
    elif sell_count >= 3 and sell_count > buy_count:
        final_statement = "SELL"
    else:
        final_statement = "HOLD"
    
    return {
        "final_statement": final_statement,
        "analysis": {
            "RSI": rsi_analysis,
            "Candle": candle_analysis,
            "MA": ma_analysis,
            "MACD": macd_analysis,
            "BB": bb_analysis
        }
    }


