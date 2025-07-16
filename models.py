from pydantic import BaseModel
from typing import List

class CandleData(BaseModel):
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]

class ChartConfig(BaseModel):
    show_ma: bool = False
    show_bb: bool = False
    show_ich: bool = False
    show_rsi: bool = False
    show_macd: bool = False
    symbol: str
    start_date: str
    end_date: str
