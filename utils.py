import uuid
import base64
import requests
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def update_attachment(file_path=None, base64String=None, ext="png", attachmentField=None):
    """Upload file to attachment service"""
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

def fetch_stock_data(symbol: str, start_date: str = None, end_date: str = None):
    """Fetch stock data from API"""
    filters = [
        {"stock_code": {"stockCode": {"$eq": symbol.upper()}}}
    ]
    
    # Apply date filter only if both dates are provided
    if start_date and end_date:
        filters.append({"time": {"$dateBetween": [f"{start_date} 00:00:00", f"{end_date} 00:00:00"]}})
    
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
    
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()["data"]


def get_trading_days_between(start_date: datetime, end_date: datetime):
    """
    Get estimated number of trading days between two dates.
    Simple estimation: count weekdays (Monday-Friday) between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Estimated number of trading days
    """
    # Ensure start_date and end_date are datetime objects
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Count all days
    all_days = (end_date - start_date).days + 1
    
    # Count weekends (Saturday and Sunday)
    weekend_count = 0
    current_date = start_date
    while current_date <= end_date:
        if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
            weekend_count += 1
        current_date += timedelta(days=1)
    
    # Trading days = all days - weekend days
    trading_days = all_days - weekend_count
    
    # Không trừ ngày lễ trong phiên bản đơn giản này để có kết quả chính xác hơn
    # Vì API đã không trả về dữ liệu cho ngày lễ rồi
    
    # Return estimated number of trading days
    return max(0, trading_days)


def get_start_date_for_trading_days(end_date: datetime, num_trading_days: int):
    """
    Calculate the start date that would give us the requested number of trading days
    back from end_date.
    
    Algorithm:
    1. Start from end_date
    2. Go backwards day by day
    3. Count only weekdays (Mon-Fri) until we reach the required number of trading days
    
    Args:
        end_date: End date
        num_trading_days: Number of trading days to go back
    
    Returns:
        Start date that would provide the requested number of trading days
    """
    # Chuẩn hóa ngày kết thúc (loại bỏ giờ, phút, giây)
    current_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
    count = 0
    
    # Danh sách ngày lễ có thể được thêm vào đây nếu cần
    # holidays = [...] # Đặt trong định dạng 'YYYY-MM-DD'
    
    # Lặp ngược ngày cho đến khi đếm đủ số ngày giao dịch
    while count < num_trading_days:
        # Giảm ngày đi 1
        current_date -= timedelta(days=1)
        
        # Kiểm tra xem có phải ngày giao dịch không (thứ 2 đến thứ 6)
        # weekday() trả về 0=Thứ Hai, 1=Thứ Ba, ..., 6=Chủ Nhật
        is_weekday = current_date.weekday() < 5  # Thứ 2-6
        
        # Kiểm tra xem có phải ngày lễ không
        # is_holiday = current_date.strftime('%Y-%m-%d') in holidays
        
        # Nếu là ngày giao dịch (ngày trong tuần và không phải ngày lễ)
        if is_weekday:  # and not is_holiday
            count += 1
            
    # Khi thoát khỏi vòng lặp, current_date sẽ là ngày bắt đầu cần tìm
    return current_date.date()
    
    return start_date.date()
