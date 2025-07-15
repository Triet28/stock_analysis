import plotly.graph_objects as go

def add_moving_averages_traces(fig, df, row=1, col=1):
    """Add Moving Averages traces to figure"""
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MA10'], 
        mode='lines', 
        line=dict(color='#694fa9'), 
        name='MA10'
    ), row=row, col=col)
    
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MA50'], 
        mode='lines', 
        line=dict(color='#7ccaf2'), 
        name='MA50'
    ), row=row, col=col)
    
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MA100'], 
        mode='lines', 
        line=dict(color='#e15545'), 
        name='MA100'
    ), row=row, col=col)
    
    fig.add_trace(go.Scatter(
        x=df['Date'], 
        y=df['MA200'], 
        mode='lines', 
        line=dict(color='#51b41f'), 
        name='MA200'
    ), row=row, col=col)
    
    return fig
