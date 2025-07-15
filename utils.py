import uuid
import base64
import requests
import os
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
