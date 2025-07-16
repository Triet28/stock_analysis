# Stock Analysis API

API phân tích cổ phiếu với các chỉ báo kỹ thuật (Technical Analysis) được xây dựng bằng FastAPI và Plotly.

## Tính năng

- **Biểu đồ nến (Candlestick Chart)**: Hiển thị giá mở, đóng, cao, thấp
- **Chỉ báo kỹ thuật**:
  - Moving Averages (MA10, MA50, MA100, MA200)
  - Bollinger Bands (20-period, 2 std dev)
  - Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
- **Volume Chart**: Hiển thị khối lượng giao dịch
- **Export PNG**: Tự động upload và trả về URL hình ảnh

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd stock_analysis
```

### 2. Tạo Python virtual environment

```bash
python -m venv .venv
```

### 3. Kích hoạt virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Thoát virtual environment:**
```bash
deactivate
```

### 4. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 5. Cấu hình environment variables

Tạo file `.env` trong thư mục gốc với nội dung:

```properties
# Long-lived admin token for attachment uploads
ATTACHMENT_TOKEN=your_attachment_token_here

# Token for trade data API
TRADE_DATA_TOKEN=your_trade_data_token_here

# API Base URL
API_BASE_URL=https://stock-agentic.digiforce.vn
```

## Cách chạy server

### 1. Chạy development server

```bash
python candlestick_chart.py
```

Hoặc sử dụng uvicorn:

```bash
uvicorn candlestick_chart:app --host 0.0.0.0 --port 8000
```

### 2. Truy cập API

Server sẽ chạy tại: `http://localhost:8000`

- **API Documentation**: `http://localhost:8000/docs`
- **Alternative docs**: `http://localhost:8000/redoc`

## Cách sử dụng API

### Endpoint chính

```
POST /plot
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| symbol | string | Yes | Mã cổ phiếu (VD: FPT, VNM, HPG) |
| startDate | string | No | Ngày bắt đầu (YYYY-MM-DD) |
| endDate | string | No | Ngày kết thúc (YYYY-MM-DD) |
| MA | boolean | No | Hiển thị Moving Averages |
| BB | boolean | No | Hiển thị Bollinger Bands |
| ICH | boolean | No | Hiển thị Ichimoku Cloud |
| RSI | boolean | No | Hiển thị RSI |
| MACD | boolean | No | Hiển thị MACD |

### Ví dụ sử dụng

#### 1. Biểu đồ nến đơn giản

```bash
curl -X POST "http://localhost:8000/plot?symbol=FPT"
```

#### 2. Biểu đồ với Moving Averages và RSI

```bash
curl -X POST "http://localhost:8000/plot?symbol=FPT&MA=true&RSI=true"
```

#### 3. Biểu đồ với tất cả chỉ báo trong khoảng thời gian cụ thể

```bash
curl -X POST "http://localhost:8000/plot?symbol=FPT&startDate=2025-01-01&endDate=2025-07-08&MA=true&BB=true&ICH=true&RSI=true&MACD=true"
```

#### 4. Sử dụng với Python requests

```python
import requests

url = "http://localhost:8000/plot"
params = {
    "symbol": "FPT",
    "startDate": "2025-01-01",
    "endDate": "2025-07-08",
    "MA": True,
    "RSI": True,
    "MACD": True
}

response = requests.post(url, params=params)
result = response.json()
print(f"Chart URL: {result['upload_result']}")
```

## Cấu trúc dự án

```
stock_analysis/
├── candlestick_chart.py     # Main FastAPI application
├── models.py                # Data models và chart config
├── utils.py                 # Utility functions (API calls, file operations)
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── README.md               # Documentation
├── indicators/             # Technical indicators calculations
│   ├── moving_averages.py
│   ├── bollinger_bands.py
│   ├── ichimoku.py
│   ├── rsi.py
│   └── macd.py
└── plotting/               # Chart plotting functions
    ├── candlestick.py
    ├── volume.py
    ├── moving_averages.py
    ├── bollinger_bands.py
    ├── ichimoku.py
    ├── rsi.py
    └── macd.py
```

## Response Format

API trả về JSON với định dạng:

```json
{
    "message": "✅ Vẽ biểu đồ và upload thành công",
    "upload_result": "https://stock-agentic.digiforce.vn/api/attachments/view/xxxxx"
}
```

## Troubleshooting

### Lỗi 401 Unauthorized

- Kiểm tra token trong file `.env`
- Đảm bảo token chưa hết hạn

### Lỗi không tìm thấy dữ liệu

- Kiểm tra mã cổ phiếu có đúng không
- Thử với khoảng thời gian khác
- Đảm bảo có dữ liệu trong khoảng thời gian yêu cầu

### Lỗi import module

- Đảm bảo đã kích hoạt virtual environment
- Cài đặt lại dependencies: `pip install -r requirements.txt`

## Dependencies

Xem file `requirements.txt` để biết danh sách đầy đủ các dependencies.

Các thư viện chính:
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `pandas`: Data manipulation
- `plotly`: Interactive charting
- `ta`: Technical analysis indicators
- `python-dotenv`: Environment variables
- `requests`: HTTP client