# Stock Analysis API & Telegram Bot

Hệ thống phân tích cổ phiếu toàn diện với các chỉ báo kỹ thuật (Technical Analysis) được xây dựng bằng FastAPI, Plotly và Telegram Bot.

## Tính năng

- **Biểu đồ nến (Candlestick Chart)**: Hiển thị giá mở, đóng, cao, thấp
- **Chỉ báo kỹ thuật**:
  - Moving Averages (MA10, MA50, MA100, MA200)
  - Bollinger Bands (20-period, 2 std dev)
  - Ichimoku Cloud (Tenkan, Kijun, Senkou A/B, Chikou)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Support & Resistance (Hỗ trợ & Kháng cự)
- **Phân tích xu hướng**: Tự động phân tích xu hướng giá theo tuần
- **Volume Chart**: Hiển thị khối lượng giao dịch
- **Export PNG**: Tự động upload và trả về URL hình ảnh
- **Phân tích dự đoán**: Đưa ra khuyến nghị BUY/SELL/HOLD dựa trên phân tích đa chỉ báo
- **Telegram Bot**: Giao diện tương tác tiện lợi để phân tích và theo dõi cổ phiếu

## Cài đặt

### 1. Clone repository

```bash
git clone <repository-url>
cd stock_analysis
```

### 2. Cài đặt Python virtual environment

#### Tại sao cần virtual environment?
- **Cô lập dependencies**: Tránh xung đột giữa các dự án khác nhau
- **Quản lý phiên bản**: Kiểm soát chính xác phiên bản các thư viện
- **Reproducibility**: Đảm bảo môi trường nhất quán giữa các máy khác nhau

#### Kiểm tra Python version
```bash
python --version
# Cần Python 3.8+ (khuyến nghị Python 3.10+)
```

#### Tạo virtual environment
```bash
# Tạo môi trường ảo với tên .venv
python -m venv .venv

# Hoặc với tên khác
python -m venv myenv
```

### 3. Kích hoạt virtual environment

**Windows (PowerShell/CMD):**
```bash
.venv\Scripts\activate
```

**macOS/Linux (Bash/Zsh):**
```bash
source .venv/bin/activate
```

**Kiểm tra đã kích hoạt thành công:**
- Prompt sẽ hiển thị `(.venv)` ở đầu dòng
- Chạy `which python` (Linux/macOS) hoặc `where python` (Windows) để xác nhận đường dẫn

**Thoát virtual environment:**
```bash
deactivate
```

#### Troubleshooting Virtual Environment

**Lỗi "execution policy" trên Windows:**
```bash
# Chạy PowerShell với quyền admin và thực hiện:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Sau đó thử lại:
.venv\Scripts\activate
```

**Lỗi "python not found":**
```bash
# Thử với python3
python3 -m venv .venv
python3 -m pip install -r requirements.txt
```

**Tái tạo virtual environment:**
```bash
# Xóa thư mục cũ
rm -rf .venv  # Linux/macOS
rmdir /s .venv  # Windows

# Tạo lại
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 4. Cài đặt dependencies

**Lưu ý:** Luôn kích hoạt virtual environment trước khi cài đặt!

```bash
# Đảm bảo đã kích hoạt venv (có (.venv) ở đầu prompt)
pip install -r requirements.txt

# Kiểm tra cài đặt thành công
pip list
pip show fastapi plotly pandas
```

**Cập nhật pip (nếu cần):**
```bash
python -m pip install --upgrade pip
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

**⚠️ Lưu ý quan trọng:** Luôn kích hoạt virtual environment trước khi chạy server!

### 1. Chạy development server

```bash
# Bước 1: Kích hoạt virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Bước 2: Chạy server
python candlestick_chart.py
```

Hoặc sử dụng uvicorn:

```bash
# Cách 1: Chạy với reload (development)
uvicorn candlestick_chart:app --reload --host 0.0.0.0 --port 8000

# Cách 2: Chạy production
uvicorn candlestick_chart:app --host 0.0.0.0 --port 8000
```

### 2. Chạy ứng dụng

Ứng dụng có thể chạy API server, Telegram Bot hoặc cả hai cùng lúc.

#### Sử dụng script run.py

```bash
# Kích hoạt virtual environment
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Chạy cả API server và Telegram Bot
python run.py --service both

# Chỉ chạy API server
python run.py --service api --port 8080

# Chỉ chạy Telegram Bot
python run.py --service bot

# Kiểm tra môi trường
python run.py --check
```

#### Chạy riêng từng thành phần

Trước khi chạy bot, đảm bảo đã thêm các biến môi trường sau vào file `.env`:

```properties
# Telegram Bot Token (từ BotFather)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# URL của API server
SERVER_URL=http://localhost:8000
```

Chạy API server:
```bash
python -m uvicorn candlestick_chart:app --reload --host 0.0.0.0 --port 8000
```

Chạy Telegram Bot:
```bash
# Đảm bảo đã kích hoạt virtual environment
python telegram_bot.py
```

### 2. Truy cập API

Server sẽ chạy tại: `   `

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
| SR | boolean | No | Hiển thị Support & Resistance |

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
curl -X POST "http://localhost:8000/plot?symbol=FPT&startDate=2025-01-01&endDate=2025-07-08&MA=true&BB=true&ICH=true&RSI=true&MACD=true&SR=true"
```

#### 4. Biểu đồ với Support & Resistance

```bash
curl -X POST "http://localhost:8000/plot?symbol=FPT&SR=true"
```

#### 5. Sử dụng với Python requests

```python
import requests

url = "http://localhost:8000/plot"
params = {
    "symbol": "FPT",
    "startDate": "2025-01-01",
    "endDate": "2025-07-08",
    "MA": True,
    "RSI": True,
    "MACD": True,
    "SR": True
}

response = requests.post(url, params=params)
result = response.json()
print(f"Chart URL: {result['upload_result']}")
```

## Telegram Bot

### Các lệnh có sẵn

- **/start** - Khởi động bot và hiển thị hướng dẫn
- **/help** - Hiển thị trợ giúp chi tiết
- **/predict [mã CK] [short/long]** - Phân tích và đưa ra khuyến nghị
  - VD: `/predict FPT short`
- **/chart [mã CK]** - Hiển thị biểu đồ kỹ thuật
  - VD: `/chart VNM`

### Tính năng Telegram Bot

- **Phân tích kỹ thuật**: Sử dụng 5 chỉ báo kỹ thuật phổ biến
- **Biểu đồ trực quan**: Hiển thị biểu đồ candlestick với đầy đủ chỉ báo
- **Phát hiện mẫu hình nến**: Nhận diện và giải thích các mẫu hình nến quan trọng
- **Giao diện tương tác**: Sử dụng nút (buttons) để tương tác dễ dàng
- **Phân tích theo khung thời gian**: Lựa chọn phân tích ngắn hạn hoặc dài hạn

## Cấu trúc dự án

```
stock_analysis/
├── candlestick_chart.py     # Main FastAPI application
├── models.py                # Data models và chart config
├── utils.py                 # Utility functions (API calls, file operations)
├── telegram_bot.py          # Telegram Bot interface
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables
├── README.md                # Documentation
├── indicators/              # Technical indicators calculations
│   ├── moving_averages.py
│   ├── bollinger_bands.py
│   ├── ichimoku.py
│   ├── rsi.py
│   ├── macd.py
│   ├── support.py           # Support level calculations
│   ├── resistance.py        # Resistance level calculations
│   └── trend_analysis.py    # Weekly trend analysis
├── prediction/              # Prediction & signal analysis
│   ├── rsi_signal_analysis.py
│   ├── macd_signal_analysis.py
│   └── future_prediction.py
└── plotting/                # Chart plotting functions
    ├── candlestick.py
    ├── volume.py
    ├── moving_averages.py
    ├── bollinger_bands.py
    ├── ichimoku.py
    ├── rsi.py
    ├── macd.py
    ├── support.py           # Support level plotting
    └── resistance.py        # Resistance level plotting
```

## Response Format

API trả về JSON với định dạng:

```json
{
    "message": "✅ Vẽ biểu đồ và upload thành công",
    "upload_result": "https://stock-agentic.digiforce.vn/api/attachments/view/xxxxx",
    "trend": [
        {
            "symbol": "FPT",
            "period": "02/01/2025 to 06/01/2025",
            "trend": "uptrend",
            "percent_change": 2.5
        },
        {
            "symbol": "FPT", 
            "period": "09/01/2025 to 13/01/2025",
            "trend": "downtrend",
            "percent_change": -1.8
        },
        {
            "symbol": "FPT",
            "period": "16/01/2025 to 20/01/2025", 
            "trend": "sideways trend",
            "percent_change": 0.3
        }
    ],
    "trend_summary": {
        "total_weeks": 27,
        "uptrend_weeks": 7,
        "downtrend_weeks": 9,
        "sideways_weeks": 11,
        "dominant_trend": "sideways trend"
    }
}
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

### Lỗi Telegram Bot

- Đảm bảo đã đúng `TELEGRAM_BOT_TOKEN` trong file `.env`
- Kiểm tra `SERVER_URL` đã đúng và server API đang chạy
- Kiểm tra kết nối internet và quyền truy cập vào API Telegram

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
- `python-telegram-bot`: Thư viện Telegram Bot API

## Screenshots

> Note: Add your own screenshots to the `/screenshots` folder to display them in the README.

### Telegram Bot

![Telegram Bot Preview](/screenshots/telegram_bot_preview.png)

### API Documentation

![API Documentation](/screenshots/api_docs.png)

### Candlestick Chart

![Candlestick Chart](/screenshots/candlestick_chart.png)

## License

[MIT License](LICENSE)