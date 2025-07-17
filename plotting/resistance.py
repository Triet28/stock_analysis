import plotly.graph_objects as go

def add_resistance_trace(fig, df, row=1, col=1):
    """ Thêm đường kháng cự vào biểu đồ"""
    # Thêm đường kháng cự
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df['Resistance'],
        mode='lines',
        name='Resistance',
        line=dict(
            color='red',
            width=2,
            dash='dash'
        ),
        hovertemplate='<b>Resistance</b><br>' +
                      'Date: %{x}<br>' +
                      'Level: %{y:.2f}<br>' +
                      '<extra></extra>'
    ), row=row, col=col)
    
    return fig