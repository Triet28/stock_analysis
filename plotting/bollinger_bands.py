import plotly.graph_objects as go

def add_bollinger_bands_traces(fig, df, row=1, col=1):
    """Add Bollinger Bands traces to figure"""
    # Upper band (invisible line for fill)
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['BB_Upper'],
        mode='lines',
        line=dict(color='rgba(32,134,213,0.5)', width=1),
        showlegend=False,
        name='BB Upper'
    ), row=row, col=col)
    
    # Lower band with fill to upper band
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['BB_Lower'],
        mode='lines',
        line=dict(color='rgba(32,134,213,0.5)', width=1),
        fill='tonexty',
        fillcolor='rgba(32,134,213,0.3)',
        name='Bollinger Bands',
        showlegend=True
    ), row=row, col=col)
    
    # Middle band (SMA20)
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['BB_Middle'],
        mode='lines',
        line=dict(color='#ffa500', width=1, dash='dash'),
        name='BB Middle (SMA20)'
    ), row=row, col=col)
    
    return fig
