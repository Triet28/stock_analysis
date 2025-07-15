from fastapi import FastAPI, Query, HTTPException
from typing import Optional
import pandas as pd
import os
from dotenv import load_dotenv

from models import CandleData, ChartConfig
from utils import fetch_stock_data
from plotting.chart_builder import build_chart

# Load environment variables
load_dotenv()

app = FastAPI(title="Stock Analysis API", description="API for stock candlestick charts with technical indicators")

@app.get("/")
def root():
    return {"message": "Stock Analysis API is running"}

@app.post("/plot")
def plot_candlestick_symbol(
        symbol: str = Query(..., description="Stock symbol"),
        startDate: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
        endDate: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
        MA: bool = Query(False, description="Show Moving Averages (MA10, MA50, MA100, MA200)"),
        BB: bool = Query(False, description="Show Bollinger Bands (20-period, 2 std dev)"),
        ICH: bool = Query(False, description="Show Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)"),
        RSI: bool = Query(False, description="Show Relative Strength Index (RSI)")):
    
    try:
        # Fetch data
        data = fetch_stock_data(symbol, startDate, endDate)
        
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
            show_ma=MA,
            show_bb=BB,
            show_ich=ICH,
            show_rsi=RSI,
            symbol=symbol.upper(),
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
