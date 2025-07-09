# pip install fastapi uvicorn plotly pandas kaleido

# {
#   "dates": ["2023-01-03", "2023-01-06", "2023-01-10", "2023-01-12", "2023-01-15",
#             "2023-01-18", "2023-01-21", "2023-01-25", "2023-01-28", "2023-01-30"],
#   "open": [100, 102, 101, 105, 107, 106, 108, 110, 109, 111],
#   "high": [105, 104, 106, 108, 110, 109, 112, 113, 115, 117],
#   "low":  [98, 100, 99, 103, 104, 103, 105, 107, 106, 109],
#   "close":[102, 101, 105, 107, 108, 107, 111, 112, 114, 116],
#   "volume":[1000,1200,1100,1500,1600,1550,1700,1800,1750,1900]
# }

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

app = FastAPI()

class CandleData(BaseModel):
    dates: list
    open: list
    high: list
    low: list
    close: list
    volume: list

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
        url="https://stock-agentic.digiforce.vn/api/attachments:create",
        headers={
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsInJvbGVOYW1lIjoiYWRtaW4iLCJpYXQiOjE3NTE5NzA3OTUsImV4cCI6MzMzMDk1NzA3OTV9.CtncBevzxc4nphny9yFyyT3So7L1kliaMZGrr1WhF6s",
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
    if startDate and endDate:
        filters.append({"time": {"$dateBetween": [f"{startDate} 00:00:00", f"{endDate} 00:00:00"]}})
    
    filter_str = requests.utils.quote(str({"$and": filters}).replace("'", '"'))
    url = (
        f"https://stock-agentic.digiforce.vn/api/trade_data:list"
        f"?pageSize=365&page=1&appends[]=stock_code"
        f"&filter={filter_str}"
        f"&fields=open,close,high,low,volume,time"
    )
    headers = {
        'authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjIsInRlbXAiOnRydWUsImlhdCI6MTc1MTk2OTUyNywic2lnbkluVGltZSI6MTc1MTk2OTUyNzU2MywiZXhwIjoxNzUyMDU1OTI3LCJqdGkiOiI5NmVmNTFmYi01NzkzLTRmNWUtYTIwZC1hODU1MTkyOTdlYjkifQ.XTIw48yEz2ZK7AVjkvFT8jLspStQDUl-dfnw5Tlic-U'
    }
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json()["data"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi lấy dữ liệu từ API: {str(e)}")
    if not data or len(data) < 2:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu hoặc dữ liệu không đủ để vẽ biểu đồ.")
    # Chuyển đổi dữ liệu về dạng CandleData
    candle_data = {
        "dates": [item["time"] for item in data],
        "open": [item["open"] for item in data],
        "high": [item["high"] for item in data],
        "low": [item["low"] for item in data],
        "close": [item["close"] for item in data],
        "volume": [item["volume"] for item in data],
    }

    # Tạo đối tượng CandleData và gọi hàm vẽ chart như cũ
    return plot_candlestick(CandleData(**candle_data), symbol)

def plot_candlestick(data: CandleData, symbol: str):
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
    df['VolumeColor'] = ['red' if c < o else 'blue' for c, o in zip(df['Close'], df['Open'])]

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7, 0.3], vertical_spacing=0.03)

    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='green',
        decreasing_line_color='red',
        name='Giá'), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA10'], mode='lines', line=dict(color='purple'), name='MA10'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA50'], mode='lines', line=dict(color='blue'), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA100'], mode='lines', line=dict(color='orange'), name='MA100'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MA200'], mode='lines', line=dict(color='red'), name='MA200'), row=1, col=1)

    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume', marker_color=df['VolumeColor']), row=2, col=1)

    fig.update_layout(
        title=f'Candlestick Chart for Stock {symbol}',
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

    url = "https://stock-agentic.digiforce.vn"+upload_result["data"]["url"]

    if os.path.exists(output_file):
        os.remove(output_file)

    return {
        "message": "✅ Vẽ biểu đồ và upload thành công",
        "upload_result": url
    }
