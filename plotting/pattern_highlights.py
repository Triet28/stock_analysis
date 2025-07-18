import plotly.graph_objects as go
import pandas as pd
from typing import Dict

# Cấu hình màu sắc cho từng pattern
PATTERN_COLORS = {
    'Doji': '#FF1B1C',                    # Vàng - Neutral signal
    'Star Doji': '#FFD700',               # Cam - Strong reversal
    'Long Legged Doji': '#9B5DE5',        # Cam đậm - High volatility
    'Dragonfly Doji': '#FF69B4',          # Xanh lá - Bullish reversal
    'Gravestone Doji': '#A52A2A',         # Đỏ - Bearish reversal
    'Marubozu': '#40E0D0',                # Tím - Strong trend
    'Spinning Top': '#EDEEC9',            # Xám - Indecision
    'Hammer': '#77BFA3',                  # Xanh đậm - Bullish reversal
    'Hanging Man': '#1E90FF',             # Đỏ đậm - Bearish reversal
    'Inverted Hammer': '#CFF27E',         # Xanh nhạt - Potential bullish
    'Shooting Star': '#B098A4'            # Hồng - Bearish reversal
}

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
        'highlight_doji': 'Doji',
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
    
    if not patterns_to_highlight:
        return fig
    
    # Tìm các ngày có patterns cần highlight
    highlighted_dates = df_with_patterns[
        df_with_patterns['candle_pattern'].isin(patterns_to_highlight)
    ]
    
    if highlighted_dates.empty:
        return fig
    
    # Thêm square markers cho từng pattern
    added_to_legend = set()  # Tránh duplicate legend entries
    
    for _, row in highlighted_dates.iterrows():
        pattern = row['candle_pattern']
        date = row['Date']
        high_price = row['High']  # Lấy giá High của nến
        color = PATTERN_COLORS.get(pattern, '#FFD700')
        
        # Thêm hình vuông nhỏ ở trên nến
        add_pattern_square_marker(fig, date, high_price, pattern, color, added_to_legend)
    
    return fig

def add_pattern_square_marker(fig, date, high_price, pattern, color, added_to_legend):
    """Thêm một hình vuông nhỏ ở đầu trên của nến cho pattern cụ thể"""
    
    # Tính toán vị trí hình vuông
    # Đặt hình vuông cách nến khoảng 3% giá trị High
    square_y = high_price * 1.005  # Cách nến 3%
    
    # Xác định xem có nên thêm vào legend không
    show_in_legend = pattern not in added_to_legend
    if show_in_legend:
        added_to_legend.add(pattern)
    
    # Vẽ hình vuông nhỏ
    fig.add_scatter(
        x=[date],  # Chỉ một điểm
        y=[square_y],  # Vị trí trên nến
        mode='markers',
        marker=dict(
            symbol='square',  # Hình vuông
            size=4,  # Kích thước nhỏ gọn
            color=color,
            line=dict(
                color='white',
                width=1
            )
        ),
        showlegend=show_in_legend,  # Chỉ hiển thị legend cho lần đầu tiên
        name=f"{pattern} Pattern",  # Tên hiển thị trong legend
        hoverinfo='text',
        hovertext=f"{pattern}<br>Date: {date}",
        row=1,
        col=1,
        legendgroup=pattern  # Nhóm các markers cùng pattern
    )

def get_highlighted_pattern_summary(df_with_patterns, config):
    """Tạo summary về các patterns được highlight"""
    
    pattern_mapping = {
        'highlight_doji': 'Doji',
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
                highlighted_summary[pattern_name] = {
                    "count": count,
                    "dates": dates,
                    "color": PATTERN_COLORS.get(pattern_name, '#FFD700')
                }
    
    return highlighted_summary
