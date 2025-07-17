import plotly.graph_objects as go

def add_support_trace(fig, df, row=1, col=1):
    """Thêm đường hỗ trợ vào biểu đồ"""
    # Thêm đường hỗ trợ
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Support'],
        mode='lines',
        name='Support',
        line=dict(
            color='green',
            width=2,
            dash='dash'
        ),
        hovertemplate='<b>Support</b><br>' +
                      'Date: %{x}<br>' +
                      'Level: %{y:.2f}<br>' +
                      '<extra></extra>'
    ), row=row, col=col)
    
    return fig