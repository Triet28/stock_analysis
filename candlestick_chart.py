import traceback
from fastapi import FastAPI, Query, HTTPException
from typing import Optional
import pandas as pd
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os
import datetime

from models import CandleData, ChartConfig, ChartRequest, PredictRequest
from utils import fetch_stock_data, update_attachment
from indicators.moving_averages import calculate_moving_averages
from indicators.bollinger_bands import calculate_bollinger_bands
from indicators.ichimoku import calculate_ichimoku
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.support import calculate_support
from indicators.resistance import calculate_resistance
from indicators.trend_analysis import calculate_trend, get_trend_summary
from indicators.candle_patterns import analyze_candle_patterns, classify_candle_pattern
from plotting.candlestick import add_candlestick_trace
from plotting.bollinger_bands import add_bollinger_bands_traces
from plotting.ichimoku import add_ichimoku_traces
from plotting.moving_averages import add_moving_averages_traces
from plotting.rsi import add_rsi_traces
from plotting.macd import add_macd_traces
from plotting.volume import add_volume_trace
from plotting.support import add_support_trace
from plotting.resistance import add_resistance_trace
from plotting.pattern_highlights import add_pattern_highlights, get_highlighted_pattern_summary
from prediction.future_prediction import predict_future_trend

load_dotenv()

app = FastAPI(title="Stock Analysis API", description="API for stock candlestick charts with technical indicators")

def build_chart(data: CandleData, config: ChartConfig, exchange: str = "Unknown"):
    """Build complete chart with all indicators"""
    # Prepare DataFrame
    df = pd.DataFrame({
        'Date': pd.to_datetime(data.dates, utc=True, errors='coerce'),
        'Open': data.open,
        'High': data.high,
        'Low': data.low,
        'Close': data.close,
        'Volume': data.volume,
    })
    df = df.dropna(subset=['Date'])
    df = df.sort_values('Date')
    df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
    
    # Calculate indicators
    if config.show_ma:
        df = calculate_moving_averages(df)
    
    if config.show_bb:
        df = calculate_bollinger_bands(df)
    
    if config.show_ich:
        df = calculate_ichimoku(df)
    
    if config.show_rsi:
        df = calculate_rsi(df)
    
    if config.show_macd:
        df = calculate_macd(df)
    
    if config.show_sr:
        df = calculate_support(df)
        df = calculate_resistance(df)

    # Phân tích candle patterns nếu cần (để có data cho highlighting)
    df_with_patterns = None
    if config.show_cp or any([
        config.highlight_marubozu,
        config.highlight_spinning_top,
        config.highlight_hammer,
        config.highlight_hanging_man,
        config.highlight_inverted_hammer,
        config.highlight_shooting_star,
        config.highlight_star_doji,
        config.highlight_long_legged_doji,
        config.highlight_dragonfly_doji,
        config.highlight_gravestone_doji
    ]):
        # Cần trends để phân loại candle patterns chính xác
        trends = calculate_trend(df, config.symbol, config.start_date, config.end_date, exchange)
        df_with_patterns = classify_candle_pattern(df, trends)
        df = df_with_patterns  # Update main df
    
    # Create subplots - determine number of rows based on indicators
    total_rows = 2  # Price + Volume
    if config.show_rsi:
        total_rows += 1
    if config.show_macd:
        total_rows += 1
    
    if total_rows == 2:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            row_heights=[0.7, 0.3], 
            vertical_spacing=0.03
        )
    elif total_rows == 3:
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            row_heights=[0.6, 0.2, 0.2], 
            vertical_spacing=0.02
        )
    elif total_rows == 4:
        fig = make_subplots(
            rows=4, cols=1, 
            shared_xaxes=True, 
            row_heights=[0.5, 0.2, 0.15, 0.15], 
            vertical_spacing=0.02
        )
    
    # Add candlestick
    fig = add_candlestick_trace(fig, df, row=1, col=1)
    
    # Add indicators to price chart
    if config.show_bb:
        fig = add_bollinger_bands_traces(fig, df, row=1, col=1)
    
    if config.show_ich:
        fig = add_ichimoku_traces(fig, df, row=1, col=1)
    
    if config.show_ma:
        fig = add_moving_averages_traces(fig, df, row=1, col=1)
    
    # Thêm Support & Resistance
    if config.show_sr:
        fig = add_support_trace(fig, df, row=1, col=1)
        fig = add_resistance_trace(fig, df, row=1, col=1)
    
    # Add volume
    fig = add_volume_trace(fig, df, row=2, col=1)
    
    # Add RSI and MACD to appropriate rows
    current_row = 3
    if config.show_rsi:
        fig = add_rsi_traces(fig, df, row=current_row, col=1)
        current_row += 1
    
    if config.show_macd:
        fig = add_macd_traces(fig, df, row=current_row, col=1)
    
    # Thêm pattern highlights (sau khi vẽ xong tất cả indicators)
    if df_with_patterns is not None:
        fig = add_pattern_highlights(fig, df_with_patterns, config, total_rows)
    
    # Update layout
    start_display = pd.to_datetime(config.start_date).strftime('%d/%m/%Y')
    end_display = pd.to_datetime(config.end_date).strftime('%d/%m/%Y')
    
    # Calculate height based on number of indicators
    chart_height = 700
    if config.show_rsi:
        chart_height += 100
    if config.show_macd:
        chart_height += 100
    
    # Set fixed dark background theme với grid rõ ràng cho đo đạc
    fig.update_layout(
        title=f'Candlestick Chart for Stock {config.symbol} ({start_display} - {end_display})',
        template='plotly_dark',
        xaxis_rangeslider_visible=False,
        height=chart_height,
        paper_bgcolor='#141823',  # Màu nền toàn bộ chart
        plot_bgcolor='#141823',   # Màu nền vùng plot
        font=dict(color='white'), # Màu chữ trắng
        xaxis=dict(
            gridcolor='#3a3f4a',    # Grid màu sáng hơn để dễ thấy
            gridwidth=1,            # Độ dày grid
            showgrid=True,          # Hiển thị grid
            color='white',
            tickmode='auto',        # Tự động tạo tick marks
            mirror=True,            # Hiển thị tick ở cả 2 bên
            showline=True,          # Hiển thị border
            linecolor='#3a3f4a'
        ),
        yaxis=dict(
            gridcolor='#3a3f4a',    # Grid màu sáng hơn để dễ thấy
            gridwidth=1,            # Độ dày grid
            showgrid=True,          # Hiển thị grid
            color='white',
            tickmode='auto',        # Tự động tạo tick marks
            mirror=True,            # Hiển thị tick ở cả 2 bên
            showline=True,          # Hiển thị border
            linecolor='#3a3f4a'
        )
    )
    
    # Configure y-axis titles với grid đồng nhất
    fig.update_yaxes(
        title_text="Price", 
        row=1, col=1,
        gridcolor='#3a3f4a',
        gridwidth=1,
        showgrid=True,
        color='white',
        mirror=True,
        showline=True,
        linecolor='#3a3f4a'
    )
    fig.update_yaxes(
        title_text="Volume", 
        row=2, col=1,
        gridcolor='#3a3f4a',
        gridwidth=1,
        showgrid=True,
        color='white',
        mirror=True,
        showline=True,
        linecolor='#3a3f4a'
    )
    
    # Set y-axis titles cho indicators với grid
    current_row = 3
    if config.show_rsi:
        fig.update_yaxes(
            title_text="RSI", 
            range=[0, 100], 
            row=current_row, col=1,
            gridcolor='#3a3f4a',
            gridwidth=1,
            showgrid=True,
            color='white',
            mirror=True,
            showline=True,
            linecolor='#3a3f4a'
        )
        current_row += 1
        
    if config.show_macd:
        fig.update_yaxes(
            title_text="MACD", 
            row=current_row, col=1,
            gridcolor='#3a3f4a',
            gridwidth=1,
            showgrid=True,
            color='white',
            mirror=True,
            showline=True,
            linecolor='#3a3f4a'
        )
    
    # Configure x-axis với grid đồng nhất cho tất cả subplots
    total_rows = 2
    if config.show_rsi:
        total_rows += 1
    if config.show_macd:
        total_rows += 1
    
    # Cập nhật x-axis cho tất cả rows với grid
    for i in range(1, total_rows + 1):
        show_labels = (i == total_rows)  # Chỉ hiện labels ở row cuối
        fig.update_xaxes(
            showticklabels=show_labels, 
            row=i, col=1,
            gridcolor='#3a3f4a',
            gridwidth=1,
            showgrid=True,
            color='white',
            mirror=True,
            showline=True,
            linecolor='#3a3f4a'
        )
    
    # Save and upload
    output_file = "candlestick.png"
    fig.write_image(output_file, width=1200, height=chart_height)
    
    with open(output_file, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")
    
    upload_result = update_attachment(
        base64String=b64_image,
        ext="png",
        attachmentField="company.file"
    )
    
    url = f"{os.getenv('API_BASE_URL')}{upload_result['data']['url']}"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Prepare comprehensive response with date information
    response = {
        "message": "✅ Vẽ biểu đồ và upload thành công",
        "chart_url": url,
        "startDate": config.start_date,
        "endDate": config.end_date
    }
    
    # Add candle pattern analysis if enabled
    if config.show_cp:  # Đơn giản hóa check
        # Sử dụng df_with_patterns nếu có, nếu không thì phân tích lại
        if df_with_patterns is not None:
            candle_analysis = analyze_candle_patterns(df_with_patterns)
        else:
            candle_analysis = analyze_candle_patterns(df)
        response["candle_patterns"] = candle_analysis
    
    # Add highlighted patterns summary if any
    if df_with_patterns is not None:
        highlighted_patterns = get_highlighted_pattern_summary(df_with_patterns, config)
        if highlighted_patterns:
            response["highlighted_patterns"] = highlighted_patterns
    
    # Add trend analysis if enabled
    if config.show_tr:
        weekly_trends = calculate_trend(df, config.symbol, config.start_date, config.end_date, exchange)
        trend_summary = get_trend_summary(weekly_trends)
        response["trend_analysis"] = {
            "weekly_trends": weekly_trends,  
            "summary": trend_summary         
        }
    
    return response

@app.get("/")
def root():
    return {"message": "Stock Analysis API is running"}

@app.post("/plot")
def plot_candlestick(request: ChartRequest):
    try:
        # Ensure symbol is a string for all usages
        symbol = request.symbol.upper()

        # Fetch data
        data = fetch_stock_data(symbol, request.startDate, request.endDate)

        if not data or len(data) < 2:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu hoặc dữ liệu không đủ để vẽ biểu đồ.")

        # Extract actual date range
        dates = [pd.to_datetime(item["time"]) for item in data]
        actual_start_date = min(dates).strftime('%Y-%m-%d')
        actual_end_date = max(dates).strftime('%Y-%m-%d')
        exchange = data[0].get("stock_code", {}).get("exchange", "Unknown")

        # Convert to CandleData
        candle_data = CandleData(
            dates=[item["time"] for item in data],
            open=[item["open"] for item in data],
            high=[item["high"] for item in data],
            low=[item["low"] for item in data],
            close=[item["close"] for item in data],
            volume=[item["volume"] for item in data]
        )

        config = ChartConfig(
            show_ma=request.MA,
            show_bb=request.BB,
            show_ich=request.ICH,
            show_rsi=request.RSI,
            show_macd=request.MACD,
            show_sr=request.SR, 
            show_tr=request.TR,  
            show_cp=request.CP,  
            # Pattern highlights
            highlight_marubozu=request.highlight_marubozu,
            highlight_spinning_top=request.highlight_spinning_top,
            highlight_hammer=request.highlight_hammer,
            highlight_hanging_man=request.highlight_hanging_man,
            highlight_inverted_hammer=request.highlight_inverted_hammer,
            highlight_shooting_star=request.highlight_shooting_star,
            highlight_star_doji=request.highlight_star_doji,
            highlight_long_legged_doji=request.highlight_long_legged_doji,
            highlight_dragonfly_doji=request.highlight_dragonfly_doji,
            highlight_gravestone_doji=request.highlight_gravestone_doji,
            symbol=symbol,
            start_date=actual_start_date,
            end_date=actual_end_date
        )
        
        # Build and return chart
        return build_chart(candle_data, config, exchange)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý dữ liệu: {str(e)}")

@app.post("/predict")
def predict_stock(request: PredictRequest):
    """
    Endpoint dự đoán xu hướng tương lai dựa trên 5 phương pháp phân tích:
    RSI, Candle Patterns, Moving Averages, MACD, Bollinger Bands
    
    Args:
        request: PredictRequest với symbol và range ("short" hoặc "long")
        range: "short" - sử dụng 20 ngày giao dịch gần nhất
               "long" - sử dụng 60 ngày giao dịch gần nhất
    
    Returns:
        Dict chứa final_statement (BUY/SELL/HOLD) và analysis chi tiết từ 5 phương pháp
    """
    try:
        if not request.range or request.range.lower() not in ["short", "long"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Tham số 'range' phải là 'short' hoặc 'long', giá trị nhận được: '{request.range}'"
            )
        
        # Use our trading days utilities from utils module
        from utils import get_start_date_for_trading_days
        # Set endDate to today
        if request.endDate:
            end_date = pd.to_datetime(request.endDate, format='%Y-%m-%d')
        else:
            end_date = datetime.datetime.now()
        range_value = request.range.lower()
        
        # Calculate start date to ensure we have enough trading days
        required_trading_days = 60 if range_value == "short" else 180 
        start_date = get_start_date_for_trading_days(end_date, required_trading_days)
        
        # Format dates for API
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Fetch data - truyền đúng thứ tự start_date, end_date
        data = fetch_stock_data(request.symbol.upper(), start_date_str, end_date_str)
        
        if not data:
            raise HTTPException(
                status_code=404, 
                detail=f"Không tìm thấy dữ liệu cho mã chứng khoán '{request.symbol.upper()}' trong khoảng thời gian từ {start_date_str} đến {end_date_str}"
            )
        elif len(data) < 2:
            raise HTTPException(
                status_code=422, 
                detail=f"Dữ liệu cho mã '{request.symbol.upper()}' không đủ để phân tích. Cần ít nhất 2 điểm dữ liệu, nhận được {len(data)}."
            )
        
        # Extract actual date range và exchange
        dates = [pd.to_datetime(item["time"]) for item in data]
        data_start_date = min(dates).strftime('%Y-%m-%d')
        data_end_date = max(dates).strftime('%Y-%m-%d')
        exchange = data[0].get("stock_code", {}).get("exchange", "Unknown")
        
        # Prepare DataFrame
        df = pd.DataFrame({
            'Date': pd.to_datetime([item["time"] for item in data], utc=True, errors='coerce'),
            'Open': [item["open"] for item in data],
            'High': [item["high"] for item in data],
            'Low': [item["low"] for item in data],
            'Close': [item["close"] for item in data],
            'Volume': [item["volume"] for item in data]
        })
        df = df.dropna(subset=['Date'])
        df = df.sort_values('Date')
        df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
        
        # Calculate all indicators needed for analysis
        df = calculate_moving_averages(df)
        df = calculate_bollinger_bands(df)
        df = calculate_rsi(df)
        df = calculate_macd(df)
        df = calculate_support(df)
        df = calculate_resistance(df)
        
        # Phân tích trends trước để dùng cho candle patterns
        trends = calculate_trend(df, request.symbol.upper(), data_start_date, data_end_date, exchange)
        
        # Dự đoán tương lai với 5 phương pháp (mỗi method tự gọi indicator của mình)
        future_prediction = predict_future_trend(df, trends, exchange)
        
        # Thêm metadata cần thiết vào response
        # Ensure symbol is a string for .upper()
        response = {
            "symbol": request.symbol.upper(),
            "startDate": data_start_date,
            "endDate": data_end_date, 
            "range": request.range,
            "exchange": exchange,
            "final_statement": future_prediction["final_statement"],
            "analysis": future_prediction["analysis"]
        }
        
        return response
        
    except HTTPException as he:
        # Re-raise HTTP exceptions as they already have proper status codes and messages
        raise he
    except Exception as e:
        # Handle general exceptions with a clear error message
        error_detail = f"Lỗi khi xử lý dữ liệu hoặc dự đoán: {str(e)}"
        # Add trace for debugging if needed
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=error_detail)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8686)