from fastapi import FastAPI, HTTPException
from typing import Optional
import pandas as pd
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os

from models import CandleData, ChartConfig, ChartRequest
from utils import fetch_stock_data, update_attachment
from indicators.moving_averages import calculate_moving_averages
from indicators.bollinger_bands import calculate_bollinger_bands
from indicators.ichimoku import calculate_ichimoku
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.support import calculate_support
from indicators.resistance import calculate_resistance
from indicators.trend_analysis import calculate_weekly_trend, get_trend_summary
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

# Load environment variables
load_dotenv()

app = FastAPI(title="Stock Analysis API", description="API for stock candlestick charts with technical indicators")

def build_chart(data: CandleData, config: ChartConfig):
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
        config.highlight_doji, config.highlight_marubozu, 
        config.highlight_spinning_top, config.highlight_hammer,
        config.highlight_hanging_man, config.highlight_inverted_hammer,
        config.highlight_shooting_star, config.highlight_star_doji,
        config.highlight_long_legged_doji, config.highlight_dragonfly_doji,
        config.highlight_gravestone_doji
    ]):
        df_with_patterns = classify_candle_pattern(df)
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
    
    # Tính xu hướng giá theo tuần (chỉ khi TR=True)
    response = {
        "message": "✅ Vẽ biểu đồ và upload thành công",
        "upload_result": url
    }
    
    if config.show_tr:
        trends = calculate_weekly_trend(df, config.symbol, config.start_date, config.end_date)
        trend_summary = get_trend_summary(trends)
        response["trend"] = trends
        response["trend_summary"] = trend_summary
    
    # Phân tích mẫu nến (chỉ khi CP=True)
    if config.show_cp:
        candle_analysis = analyze_candle_patterns(df)
        response["candle_analysis"] = candle_analysis
    
    # Thêm thông tin về highlighted patterns
    if df_with_patterns is not None:
        highlighted_patterns = get_highlighted_pattern_summary(df_with_patterns, config)
        if highlighted_patterns:
            response["highlighted_patterns"] = highlighted_patterns
    
    return response

@app.get("/")
def root():
    return {"message": "Stock Analysis API is running"}

@app.post("/plot")
def plot_candlestick_symbol(request: ChartRequest):
    try:
        # Fetch data
        data = fetch_stock_data(request.symbol, request.startDate, request.endDate)
        
        if not data or len(data) < 2:
            raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu hoặc dữ liệu không đủ để vẽ biểu đồ.")
        
        # Extract actual date range
        dates = [pd.to_datetime(item["time"]) for item in data]
        actual_start_date = min(dates).strftime('%Y-%m-%d')
        actual_end_date = max(dates).strftime('%Y-%m-%d')
        
        # Convert to CandleData
        candle_data = CandleData(
            dates=[item["time"] for item in data],
            open=[item["open"] for item in data],
            high=[item["high"] for item in data],
            low=[item["low"] for item in data],
            close=[item["close"] for item in data],
            volume=[item["volume"] for item in data]
        )
        
        # Create chart config
        config = ChartConfig(
            show_ma=request.MA,
            show_bb=request.BB,
            show_ich=request.ICH,
            show_rsi=request.RSI,
            show_macd=request.MACD,
            show_sr=request.SR,
            show_tr=request.TR,
            show_cp=request.CP,
            
            # Copy pattern highlight flags
            highlight_doji=request.highlight_doji,
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
            
            symbol=request.symbol.upper(),
            start_date=actual_start_date,
            end_date=actual_end_date
        )
        
        # Build and return chart
        return build_chart(candle_data, config)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi xử lý dữ liệu: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
