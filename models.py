from pydantic import BaseModel
from typing import List, Optional

class CandleData(BaseModel):
    dates: List[str]
    open: List[float]
    high: List[float]
    low: List[float]
    close: List[float]
    volume: List[int]

class ChartRequest(BaseModel):
    symbol: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    MA: bool = False
    BB: bool = False
    ICH: bool = False
    RSI: bool = False
    MACD: bool = False
    SR: bool = False
    TR: bool = False
    CP: bool = False  # Candle Pattern Analysis
    
    # Candle Pattern Highlights
    highlight_marubozu: bool = False
    highlight_spinning_top: bool = False
    highlight_hammer: bool = False
    highlight_hanging_man: bool = False
    highlight_inverted_hammer: bool = False
    highlight_shooting_star: bool = False
    highlight_star_doji: bool = False
    highlight_long_legged_doji: bool = False
    highlight_dragonfly_doji: bool = False
    highlight_gravestone_doji: bool = False

class PredictRequest(BaseModel):
    symbol: str
    range: str = "unknown"
    endDate: Optional[str] = None

class ChartConfig(BaseModel):
    show_ma: bool = False
    show_bb: bool = False
    show_ich: bool = False
    show_rsi: bool = False
    show_macd: bool = False
    show_sr: bool = False  # Support & Resistance
    show_tr: bool = False  # Weekly Trend Analysis
    show_cp: bool = False  # Candle Pattern Analysis
    
    # Candle Pattern Highlights
    highlight_marubozu: bool = False
    highlight_spinning_top: bool = False
    highlight_hammer: bool = False
    highlight_hanging_man: bool = False
    highlight_inverted_hammer: bool = False
    highlight_shooting_star: bool = False
    highlight_star_doji: bool = False
    highlight_long_legged_doji: bool = False
    highlight_dragonfly_doji: bool = False
    highlight_gravestone_doji: bool = False
    
    symbol: str
    start_date: str
    end_date: str
