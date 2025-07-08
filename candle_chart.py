from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import os

app = Dash(__name__)

app.layout = html.Div([
    dcc.Location(id='url', refresh=True),  # Để theo dõi URL

    html.H2("📊 Candlestick Chart Generator"),

    html.Div([
        html.Label("Enter stock symbol:"),
        dcc.Input(id='symbol-input', type='text', placeholder='e.g., AAA'),
        html.Button('Go', id='go-button', n_clicks=0)
    ], style={'marginBottom': '20px'}),

    dcc.Checklist(
        id='toggle-rangeslider',
        options=[{'label': 'Include Rangeslider', 'value': 'slider'}],
        value=['slider']
    ),

    html.H4(id='chart-title'),
    dcc.Graph(id='graph')
])

# Redirect khi nhấn nút Go
@app.callback(
    Output('url', 'pathname'),
    Input('go-button', 'n_clicks'),
    State('symbol-input', 'value'),
    prevent_initial_call=True
)
def update_url(n_clicks, symbol):
    if symbol:
        return f'/{symbol.upper()}'
    return '/'

# Cập nhật biểu đồ theo URL
@app.callback(
    Output('graph', 'figure'),
    Output('chart-title', 'children'),
    Input('url', 'pathname'),
    Input('toggle-rangeslider', 'value')
)
def display_chart(pathname, slider_value):
    if not pathname or pathname == '/':
        return go.Figure(), "📢 Please enter a stock symbol above."

    symbol = pathname.strip('/').upper()
    file_path = f"C:/Users/Admin/Desktop/Study/clone_project/crawl/data/{symbol}.xlsx"

    if not os.path.exists(file_path):
        return go.Figure(), f"❌ File not found: {symbol}.xlsx"

    try:
        df = pd.read_excel(file_path)

        fig = go.Figure(go.Candlestick(
            x=df['time'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
        ))

        fig.update_layout(
            xaxis_rangeslider_visible='slider' in slider_value
        )

        return fig, f"📈 Candlestick chart for {symbol}"

    except KeyError as e:
        return go.Figure(), f"❌ Missing column: {str(e)}"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=False)
