import os
import time
import pandas as pd
import requests
from datetime import datetime

# Đường dẫn file mã công ty
symbol_file = "company_code.txt"

# Đọc mã chứng khoán
with open(symbol_file, "r", encoding="utf-8") as f:
    symbols = [line.strip() for line in f if line.strip()]

# Tạo thư mục nếu chưa có
os.makedirs("data", exist_ok=True)

# Header bắt buộc
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://cafef.vn"
}

# Lặp từng mã
for symbol in symbols:
    url = f"https://msh-devappdata.cafef.vn/rest-api/api/v1/TradingViewsData?symbol={symbol}&type=D1"
    print(f"📥 {symbol} → Tải dữ liệu mới nhất...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        raw = response.json()
        data = raw.get("data", {}).get("value", {}).get("dataInfor", [])

        if not data or not isinstance(data, list):
            print(f"⚠️ Không có dữ liệu hợp lệ cho mã {symbol}")
            continue

        # Lấy dòng đầu tiên
        latest = data[0]
        latest["time"] = pd.to_datetime(latest["time"], unit="s")
        df_new = pd.DataFrame([latest])

        file_path = f"data/{symbol}.xlsx"

        # Nếu đã có file → chèn vào đầu
        if os.path.exists(file_path):
            df_old = pd.read_excel(file_path)
            df_old["time"] = pd.to_datetime(df_old["time"])
            # Kiểm tra nếu bản ghi đã tồn tại thì không thêm nữa
            if not df_old["time"].isin([latest["time"]]).any():
                df_combined = pd.concat([df_new, df_old], ignore_index=True)
                df_combined.to_excel(file_path, index=False)
                print(f"✅ {symbol}: Đã thêm bản ghi mới vào đầu file")
            else:
                print(f"ℹ️ {symbol}: Dữ liệu ngày {latest['time'].date()} đã tồn tại, bỏ qua")
        else:
            df_new.to_excel(file_path, index=False)
            print(f"🆕 {symbol}: Tạo mới file với dòng đầu tiên")

    except Exception as e:
        print(f"❌ {symbol}: Lỗi - {e}")

    time.sleep(2)
