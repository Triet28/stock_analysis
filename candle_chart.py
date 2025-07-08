from dash import Dash, dcc, html, Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import os
import requests

app = Dash(__name__)

def update_symbol(symbol):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://cafef.vn"
    }

    url = f"https://msh-devappdata.cafef.vn/rest-api/api/v1/TradingViewsData?symbol={symbol}&type=D1"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        raw = response.json()
        data = raw.get("data", {}).get("value", {}).get("dataInfor", [])

        if not data or not isinstance(data, list):
            return f"⚠️ Không có dữ liệu hợp lệ cho mã {symbol}"

        latest = data[0]
        latest["time"] = pd.to_datetime(latest["time"], unit="s")
        df_new = pd.DataFrame([latest])

        file_path = os.path.join(os.path.dirname(__file__), "data", f"{symbol}.xlsx")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        if os.path.exists(file_path):
            df_old = pd.read_excel(file_path)
            df_old["time"] = pd.to_datetime(df_old["time"])
            if not df_old["time"].isin([latest["time"]]).any():
                df_combined = pd.concat([df_new, df_old], ignore_index=True)
                df_combined.to_excel(file_path, index=False)
                return f"✅ Đã thêm dữ liệu mới cho {symbol}"
            else:
                return f"ℹ️ {symbol}: Dữ liệu đã tồn tại, không cần cập nhật"
        else:
            df_new.to_excel(file_path, index=False)
            return f"🆕 Đã tạo file mới cho {symbol}"

    except Exception as e:
        return f"❌ Lỗi khi cập nhật {symbol}: {e}"

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

    # ✅ Cập nhật dữ liệu trước khi vẽ
    update_result = update_symbol(symbol)

    file_path = os.path.join(os.path.dirname(__file__), "data", f"{symbol}.xlsx")
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

        return fig, f"{update_result} → 📈 Chart for {symbol}"

    except KeyError as e:
        return go.Figure(), f"❌ Missing column: {str(e)}"

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=False)
