import plotly.graph_objects as go

def add_macd_traces(fig, df, row=4, col=1):
    """Add MACD traces to figure"""
    
    # MACD line (blue)
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MACD'],
        mode='lines',
        line=dict(color='#2E86AB', width=2),
        name='MACD'
    ), row=row, col=col)
    
    # Signal line (red)
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MACD_Signal'],
        mode='lines',
        line=dict(color='#F24236', width=2),
        name='Signal'
    ), row=row, col=col)
    
    # Histogram (green/red bars)
    colors = ['#00C851' if val >= 0 else '#FF4444' for val in df['MACD_Histogram']]
    fig.add_trace(go.Bar(
        x=df['Date'], 
        y=df['MACD_Histogram'],
        marker_color=colors,
        name='Histogram',
        opacity=0.7
    ), row=row, col=col)
    
    # Zero line (gray dashed)
    fig.add_trace(go.Scatter(
        x=[df['Date'].iloc[0], df['Date'].iloc[-1]], 
        y=[0, 0],
        mode='lines',
        line=dict(color='gray', width=1, dash='dash'),
        name='Zero Line',
        showlegend=True
    ), row=row, col=col)
    
    return fig
