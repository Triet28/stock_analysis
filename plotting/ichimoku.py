import plotly.graph_objects as go

def add_ichimoku_traces(fig, df, row=1, col=1):
    """Add Ichimoku Cloud traces to figure"""
    # Tenkan-sen (Conversion Line) - Red
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['ICH_Tenkan'],
        mode='lines',
        line=dict(color='#ff6b6b', width=1),
        name='Tenkan-sen (9)'
    ), row=row, col=col)
    
    # Kijun-sen (Base Line) - Blue
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['ICH_Kijun'],
        mode='lines',
        line=dict(color='#4ecdc4', width=1),
        name='Kijun-sen (26)'
    ), row=row, col=col)
    
    # Senkou Span A (Leading Span A) - Green, invisible for fill
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['ICH_SpanA'],
        mode='lines',
        line=dict(color='rgba(76, 175, 80, 0.5)', width=1),
        showlegend=False,
        name='Senkou Span A'
    ), row=row, col=col)
    
    # Senkou Span B (Leading Span B) - Orange, with fill to Span A
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['ICH_SpanB'],
        mode='lines',
        line=dict(color='rgba(255, 152, 0, 0.5)', width=1),
        fill='tonexty',
        fillcolor='rgba(158, 158, 158, 0.3)',
        name='Kumo (Cloud)',
        showlegend=True
    ), row=row, col=col)
    
    # Chikou Span (Lagging Span) - Purple
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['ICH_Chikou'],
        mode='lines',
        line=dict(color='#9c27b0', width=1, dash='dot'),
        name='Chikou Span (26)'
    ), row=row, col=col)
    
    return fig
