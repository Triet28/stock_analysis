import plotly.graph_objects as go

def add_candlestick_trace(fig, df, row=1, col=1):
    """Add candlestick trace to figure"""
    fig.add_trace(go.Candlestick(
        x=df['Date'], 
        open=df['Open'], 
        high=df['High'],
        low=df['Low'], 
        close=df['Close'],
        increasing_line_color='#00998b',
        decreasing_line_color='#ff5252',
        name='Giá'
    ), row=row, col=col)
    return fig
