from fastapi import FastAPI
from pydantic import BaseModel
from fastapi import Query, HTTPException
from plotly.subplots import make_subplots
from typing import Optional
import pandas as pd
import plotly.graph_objects as go
import uuid
import base64
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

class CandleData(BaseModel):
    dates: list
    open: list
    high: list
    low: list
    close: list
    volume: list

BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
if not BEARER_TOKEN:
    raise RuntimeError("❌ Thiếu biến môi trường BEARER_TOKEN")

def update_attachment(file_path=None, base64String=None, ext="png", attachmentField=None):
    if ext == "png":
        mime_type = "image/png"
    elif ext == "jpg":
        mime_type = "image/jpg"
    else:
        mime_type = "image/jpeg"

    if ext in ["mp3", "wav"]:
        mime_type = "audio/mpeg"

    if ext in ["mp4", "mov", "avi", "mkv", "webm", "flv", "wmv", "m4v", "m4a", "aac", "ogg", "opus", "m3u8", "m3u"]:
        mime_type = "video/mp4"

    files = []
    if file_path:
        files.append(
            (
                "file",
                (f"{uuid.uuid4()}.{ext}", open(file_path, "rb"), mime_type),
            )
        )
    else:
        files = [
            (
                "file",
                (
                    f"{uuid.uuid4()}.{ext}",
                    base64.b64decode(base64String),
                    mime_type,
                ),
            )
        ]

    response = requests.request(
        "POST",
        url=f"{os.getenv('API_BASE_URL')}/api/attachments:create",
        headers={
            "Authorization": f"Bearer {os.getenv('ATTACHMENT_TOKEN')}",
        },
        params={"attachmentField": attachmentField},
        files=files,
    )
    return response.json()

@app.post("/plot")
def plot_candlestick_symbol(
        symbol: str = Query(..., description="Stock symbol"),
        startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)")  ):
    
    filters = [
        {"stock_code": {"stockCode": {"$eq": symbol}}}
    ]
    
    # Apply date filter only if both dates are provided
    if startDate and endDate:
        filters.append({"time": {"$dateBetween": [f"{startDate} 00:00:00", f"{endDate} 00:00:00"]}})
    
    filter_str = requests.utils.quote(str({"$and": filters}).replace("'", '"'))
    url = (
        f"{os.getenv('API_BASE_URL')}/api/trade_data:list"
        f"?pageSize=365&page=1&appends[]=stock_code"
        f"&filter={filter_str}"
        f"&fields=open,close,high,low,volume,time"
    )
    headers = {
        'authorization': f"Bearer {os.getenv('TRADE_DATA_TOKEN')}"
    }
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()["data"]
    except Exception as e:
        print(resp.text)
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu từ API: {str(e)}")
    if not data or len(data) < 2:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu hoặc dữ liệu không đủ để vẽ biểu đồ.")
    
    # Extract actual date range from the response data
    dates = [pd.to_datetime(item["time"]) for item in data]
    actual_start_date = min(dates).strftime('%Y-%m-%d')  # Oldest date
    actual_end_date = max(dates).strftime('%Y-%m-%d')    # Latest date
    
    # Chuyển đổi dữ liệu về dạng CandleData
    candle_data = {
        "dates": [item["time"] for item in data],
        "open": [item["open"] for item in data],
        "high": [item["high"] for item in data],
        "low": [item["low"] for item in data],
        "close": [item["close"] for item in data],
        "volume": [item["volume"] for item in data],
    }

    # Tạo đối tượng CandleData và gọi hàm vẽ chart với date range
    return plot_candlestick(CandleData(**candle_data), symbol, actual_start_date, actual_end_date)

def plot_candlestick(data: CandleData, symbol: str, start_date: str, end_date: str):
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
    df['MA10'] = df['Close'].rolling(window=10).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA100'] = df['Close'].rolling(window=100).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    df['VolumeColor'] = ['#ff5252' if c < o else '#00998b' for c, o in zip(df['Close'], df['Open'])]
    df['VolumeColor'] = ['#ff5252' if c < o else '#00998b' for c, o in zip(df['Close'], df['Open'])]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='#00998b',
        decreasing_line_color='#ff5252',
        increasing_line_color='#00998b',
        decreasing_line_color='#ff5252',
        name='Giá'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA10'], mode='lines', line=dict(color='#694fa9'), name='MA10'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA50'], mode='lines', line=dict(color='#7ccaf2'), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA100'], mode='lines', line=dict(color='#e15545'), name='MA100'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA200'], mode='lines', line=dict(color='#51b41f'), name='MA200'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA10'], mode='lines', line=dict(color='#694fa9'), name='MA10'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA50'], mode='lines', line=dict(color='#7ccaf2'), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA100'], mode='lines', line=dict(color='#e15545'), name='MA100'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA200'], mode='lines', line=dict(color='#51b41f'), name='MA200'), row=1, col=1)

    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume', marker_color=df['VolumeColor']), row=2, col=1)

    # Format dates for display
    start_display = pd.to_datetime(start_date).strftime('%d/%m/%Y')
    end_display = pd.to_datetime(end_date).strftime('%d/%m/%Y')
    
    fig.update_layout(
        title=f'Candlestick Chart for Stock {symbol} ({start_display} - {end_display})',
        template='plotly_white',
        xaxis_rangeslider_visible=False,
        height=700,
    )

    output_file = "candlestick_ma50_ma100.png"
    fig.write_image(output_file, width=1200, height=800)

    with open(output_file, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")

    upload_result = update_attachment(
        base64String=b64_image,
        ext="png",
        attachmentField="company.file"
    )

    # return upload_result

    url = f"{os.getenv('API_BASE_URL')}{upload_result['data']['url']}"

    if os.path.exists(output_file):
        os.remove(output_file)

    return {
        "message": "✅ Vẽ biểu đồ và upload thành công",
        "upload_result": url
    }
