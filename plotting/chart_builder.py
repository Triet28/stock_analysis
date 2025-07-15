import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
import os

from models import CandleData, ChartConfig
from indicators.moving_averages import calculate_moving_averages
from indicators.bollinger_bands import calculate_bollinger_bands
from indicators.ichimoku import calculate_ichimoku
from indicators.rsi import calculate_rsi
from plotting.candlestick import add_candlestick_trace
from plotting.bollinger_bands import add_bollinger_bands_traces
from plotting.ichimoku import add_ichimoku_traces
from plotting.moving_averages import add_moving_averages_traces
from plotting.rsi import add_rsi_traces
from plotting.volume import add_volume_trace
from utils import update_attachment

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
    
    # Create subplots
    if config.show_rsi:
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            row_heights=[0.6, 0.2, 0.2], 
            vertical_spacing=0.02,
        )
    else:
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            row_heights=[0.7, 0.3], 
            vertical_spacing=0.03
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
    
    # Add volume
    fig = add_volume_trace(fig, df, row=2, col=1)
    
    # Add RSI if enabled
    if config.show_rsi:
        fig = add_rsi_traces(fig, df, row=3, col=1)
    
    # Update layout
    start_display = pd.to_datetime(config.start_date).strftime('%d/%m/%Y')
    end_display = pd.to_datetime(config.end_date).strftime('%d/%m/%Y')
    
    fig.update_layout(
        title=f'Candlestick Chart for Stock {config.symbol} ({start_display} - {end_display})',
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        height=800 if config.show_rsi else 700,
    )
    
    # Update y-axis titles
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    if config.show_rsi:
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=3, col=1)
    
    # Save and upload
    output_file = "candlestick.png"
    fig.write_image(output_file, width=1200, height=900 if config.show_rsi else 800)
    
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
    
    return {
        "message": "✅ Vẽ biểu đồ và upload thành công",
        "upload_result": url
    }
