import plotly.graph_objects as go
import pandas as pd
from typing import Dict

# Cấu hình marker cho hệ thống mới (tối đa 4 markers)
MARKER_CONFIGS = [
    {"symbol": "triangle-down", "color": "#FFD700", "size": 6},      # Vàng - Star
    {"symbol": "square", "color": "#CFF27E", "size": 6},    # Xanh nhạt - Square  
    {"symbol": "diamond", "color": "#FF69B4", "size": 6},   # Hồng - Diamond
    {"symbol": "circle", "color": "#59C3C3", "size": 6}     # Vàng - Circle
]

# Cấu hình màu sắc cho từng pattern (kept for backward compatibility)
# PATTERN_COLORS = {
#     'Doji': '#FF1B1C',                    # Vàng - Neutral signal
#     'Star Doji': '#FFD700',               # Cam - Strong reversal
#     'Long Legged Doji': '#9B5DE5',        # Cam đậm - High volatility
#     'Dragonfly Doji': '#FF69B4',          # Xanh lá - Bullish reversal
#     'Gravestone Doji': '#A52A2A',         # Đỏ - Bearish reversal
#     'Marubozu': '#40E0D0',                # Tím - Strong trend
#     'Spinning Top': '#EDEEC9',            # Xám - Indecision
#     'Hammer': '#77BFA3',                  # Xanh đậm - Bullish reversal
#     'Hanging Man': '#1E90FF',             # Đỏ đậm - Bearish reversal
#     'Inverted Hammer': '#CFF27E',         # Xanh nhạt - Potential bullish
#     'Shooting Star': '#B098A4'            # Hồng - Bearish reversal
# }

def add_pattern_highlights(fig, df_with_patterns, config, total_rows=2):
    """
    Thêm hình vuông nhỏ ở đầu trên nến để highlight các candle patterns
    
    Args:
        fig: Plotly figure object
        df_with_patterns: DataFrame đã có cột 'candle_pattern'
        config: ChartConfig với các highlight flags
        total_rows: Số lượng subplot
    """
    
    # Mapping từ config flags đến pattern names
    pattern_mapping = {
        'highlight_marubozu': 'Marubozu', 
        'highlight_spinning_top': 'Spinning Top',
        'highlight_hammer': 'Hammer',
        'highlight_hanging_man': 'Hanging Man',
        'highlight_inverted_hammer': 'Inverted Hammer',
        'highlight_shooting_star': 'Shooting Star',
        'highlight_star_doji': 'Star Doji',
        'highlight_long_legged_doji': 'Long Legged Doji',
        'highlight_dragonfly_doji': 'Dragonfly Doji',
        'highlight_gravestone_doji': 'Gravestone Doji'
    }
    
    # Lọc các patterns cần highlight
    patterns_to_highlight = []
    for flag_name, pattern_name in pattern_mapping.items():
        if getattr(config, flag_name, False):
            patterns_to_highlight.append(pattern_name)
    
    # Kiểm tra giới hạn tối đa 4 patterns
    if len(patterns_to_highlight) > 4:
        raise ValueError(f"Tối đa chỉ được highlight 4 loại pattern. Hiện tại: {len(patterns_to_highlight)} patterns được chọn.")
    
    if not patterns_to_highlight:
        return fig
    
    # Tìm các ngày có patterns cần highlight
    highlighted_dates = df_with_patterns[
        df_with_patterns['candle_pattern'].isin(patterns_to_highlight)
    ]
    
    if highlighted_dates.empty:
        return fig
    
    # Thêm markers cho từng candle theo pattern type
    added_to_legend = set()  # Tránh duplicate legend entries
    pattern_to_marker_index = {}  # Map pattern to marker index
    
    # Gán marker index cho từng pattern type
    for idx, pattern in enumerate(patterns_to_highlight):
        pattern_to_marker_index[pattern] = idx
    
    for _, row in highlighted_dates.iterrows():
        pattern = row['candle_pattern']
        date = row['Date']
        high_price = row['High']  # Lấy giá High của nến
        
        # Lấy marker index từ pattern type
        marker_idx = pattern_to_marker_index[pattern]
        marker_config = MARKER_CONFIGS[marker_idx]
        
        # Thêm marker với cấu hình theo pattern type
        add_pattern_square_marker(fig, date, high_price, pattern, marker_config, added_to_legend, marker_idx + 1)
    
    return fig

def add_pattern_square_marker(fig, date, high_price, pattern, marker_config, added_to_legend, marker_index):
    """Thêm marker với cấu hình cố định cho pattern cụ thể"""
    
    # Tính toán vị trí marker
    # Đặt marker cách nến khoảng 0.5% giá trị High
    marker_y = high_price * 1.005  # Cách nến 0.5%
    
    # Xác định xem có nên thêm vào legend không (theo pattern type, không phải từng nến)
    show_in_legend = pattern not in added_to_legend
    if show_in_legend:
        added_to_legend.add(pattern)
    
    # Vẽ marker với cấu hình mới
    fig.add_scatter(
        x=[date],  # Chỉ một điểm
        y=[marker_y],  # Vị trí trên nến
        mode='markers',
        marker=dict(
            symbol=marker_config["symbol"],  # Hình dạng từ config
            size=marker_config["size"],      # Kích thước từ config
            color=marker_config["color"],    # Màu từ config
            line=dict(
                color='white',
                width=1
            )
        ),
        showlegend=show_in_legend,  # Chỉ hiển thị legend cho pattern type
        name=f"{pattern}",  # Tên hiển thị trong legend
        hoverinfo='text',
        hovertext=f"{pattern}<br>Date: {date}<br>Symbol: {marker_config['symbol'].upper()}",
        row=1,
        col=1,
        legendgroup=pattern  # Nhóm các markers theo pattern type
    )

def get_highlighted_pattern_summary(df_with_patterns, config):
    """Tạo summary về các patterns được highlight"""
    
    pattern_mapping = {
        'highlight_marubozu': 'Marubozu',
        'highlight_spinning_top': 'Spinning Top',
        'highlight_hammer': 'Hammer',
        'highlight_hanging_man': 'Hanging Man',
        'highlight_inverted_hammer': 'Inverted Hammer',
        'highlight_shooting_star': 'Shooting Star',
        'highlight_star_doji': 'Star Doji',
        'highlight_long_legged_doji': 'Long Legged Doji',
        'highlight_dragonfly_doji': 'Dragonfly Doji',
        'highlight_gravestone_doji': 'Gravestone Doji'
    }
    
    highlighted_summary = {}
    
    for flag_name, pattern_name in pattern_mapping.items():
        if getattr(config, flag_name, False):
            pattern_data = df_with_patterns[df_with_patterns['candle_pattern'] == pattern_name]
            count = len(pattern_data)
            if count > 0:
                dates = pattern_data['Date'].tolist()
                
                # Tìm marker index cho pattern này
                enabled_patterns = [pn for fn, pn in pattern_mapping.items() if getattr(config, fn, False)]
                if pattern_name in enabled_patterns:
                    marker_index = enabled_patterns.index(pattern_name)
                    if marker_index < len(MARKER_CONFIGS):
                        marker_config = MARKER_CONFIGS[marker_index]
                        highlighted_summary[pattern_name] = {
                            "count": count,
                            "dates": dates,
                            "marker_symbol": marker_config["symbol"],
                            "marker_color": marker_config["color"],
                            "marker_index": marker_index + 1
                        }
    
    return highlighted_summary
