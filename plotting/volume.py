import plotly.graph_objects as go

def add_volume_trace(fig, df, row=2, col=1):
    """Add Volume trace to figure"""
    df['VolumeColor'] = ['#ff5252' if c < o else '#00998b' for c, o in zip(df['Close'], df['Open'])]
    
    fig.add_trace(go.Bar(
        x=df['Date'], 
        y=df['Volume'], 
        name='Volume', 
        marker_color=df['VolumeColor']
    ), row=row, col=col)
    
    return fig
