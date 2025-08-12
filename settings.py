"""
Settings module for storing and retrieving user settings.
This module handles saving settings to a file and loading them for different users.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Path to settings file
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_settings')

# Default settings
DEFAULT_PLOT_SETTINGS = {
    "MA": False,      # Moving Averages
    "BB": False,      # Bollinger Bands
    "RSI": False,     # RSI
    "MACD": False,    # MACD
    "ICH": False,    # Ichimoku
    "SR": False,      # Support & Resistance
    "TR": False,     # Trend Analysis
    "CP": False,      # Candle Patterns
    # Candle Pattern Highlights - all off by default
    "highlight_marubozu": False,
    "highlight_spinning_top": False,
    "highlight_hammer": False,
    "highlight_hanging_man": False,
    "highlight_inverted_hammer": False,
    "highlight_shooting_star": False,
    "highlight_star_doji": False,
    "highlight_long_legged_doji": False,
    "highlight_dragonfly_doji": False,
    "highlight_gravestone_doji": False
}

def ensure_settings_directory():
    """Ensure that the settings directory exists"""
    if not os.path.exists(SETTINGS_DIR):
        os.makedirs(SETTINGS_DIR)

def get_user_settings_file(user_id: int) -> str:
    """Get the path to the user's settings file"""
    ensure_settings_directory()
    return os.path.join(SETTINGS_DIR, f"user_{user_id}.json")

def load_user_settings(user_id: int) -> Dict[str, Any]:
    """Load settings for a specific user"""
    settings_file = get_user_settings_file(user_id)
    
    if not os.path.exists(settings_file):
        # If no settings file exists, create one with default settings
        default_settings = {
            "plot": DEFAULT_PLOT_SETTINGS
        }
        save_user_settings(user_id, default_settings)
        return default_settings
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading settings for user {user_id}: {str(e)}")
        return {"plot": DEFAULT_PLOT_SETTINGS}

def save_user_settings(user_id: int, settings: Dict[str, Any]) -> bool:
    """Save settings for a specific user"""
    settings_file = get_user_settings_file(user_id)
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving settings for user {user_id}: {str(e)}")
        return False

def update_plot_settings(user_id: int, new_settings: Dict[str, Any]) -> bool:
    """Update plot settings for a specific user"""
    current_settings = load_user_settings(user_id)
    
    # Update only the specified settings
    if "plot" not in current_settings:
        current_settings["plot"] = DEFAULT_PLOT_SETTINGS
    
    candle_highlight_keys = [key for key in current_settings["plot"].keys() if key.startswith("highlight_")]
    
    for key, value in new_settings.items():
        # Nếu đang cố gắng BẬT một nến mới
        if key.startswith("highlight_") and value is True and current_settings["plot"].get(key) is False:
            # Đếm số lượng nến hiện đang bật
            active_candle_patterns = sum(1 for k in candle_highlight_keys if current_settings["plot"].get(k) is True)
            
            # Nếu đã có 4 loại nến đang bật và đang cố gắng bật thêm
            if active_candle_patterns >= 4:
                return False, "Chỉ được phép hiển thị tối đa 4 loại nến cùng lúc. Vui lòng tắt một loại nến khác trước."
        
        # Cập nhật cài đặt nếu key hợp lệ
        if key in current_settings["plot"]:
            current_settings["plot"][key] = value
    
    return save_user_settings(user_id, current_settings)

def get_plot_settings(user_id: int) -> Dict[str, Any]:
    """Get plot settings for a specific user"""
    settings = load_user_settings(user_id)
    return settings.get("plot", DEFAULT_PLOT_SETTINGS)
