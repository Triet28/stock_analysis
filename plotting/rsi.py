import plotly.graph_objects as go

def add_rsi_traces(fig, df, row=3, col=1):
    """Add RSI traces to figure"""
    # RSI line
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['RSI'],
        mode='lines',
        line=dict(color='#9c27b0', width=2),
        name='RSI (14)'
    ), row=row, col=col)
    
    # RSI reference lines as legend entries
    fig.add_trace(go.Scatter(
        x=[df['Date'].iloc[0], df['Date'].iloc[-1]], 
        y=[70, 70],
        mode='lines',
        line=dict(color='green', width=1, dash='dash'),
        name='Overbought (70)',
        showlegend=True
    ), row=row, col=col)
    
    fig.add_trace(go.Scatter(
        x=[df['Date'].iloc[0], df['Date'].iloc[-1]], 
        y=[30, 30],
        mode='lines',
        line=dict(color='red', width=1, dash='dash'),
        name='Oversold (30)',
        showlegend=True
    ), row=row, col=col)
    
    fig.add_trace(go.Scatter(
        x=[df['Date'].iloc[0], df['Date'].iloc[-1]], 
        y=[50, 50],
        mode='lines',
        line=dict(color='gray', width=1, dash='dot'),
        name='Midline (50)',
        showlegend=True
    ), row=row, col=col)
    
    return fig
