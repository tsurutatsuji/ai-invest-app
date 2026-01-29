import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from datetime import datetime

st.set_page_config(page_title="投資チャート2画面比較", layout="wide")
st.title("📊 チャート確認（複数期間比較＋ズーム・MA対応）")

# 銘柄辞書（簡略）
stock_suggestions = {
    "Apple": "AAPL", "Microsoft": "MSFT", "Amazon": "AMZN", "Google": "GOOGL", "Tesla": "TSLA"
}

crypto_suggestions = {
    "Bitcoin": "BTCUSDT", "Ethereum": "ETHUSDT", "Ripple": "XRPUSDT", "Solana": "SOLUSDT"
}

# 資産タイプ
asset_type = st.selectbox("資産タイプ", ["株式", "仮想通貨"])

# 銘柄選択（検索付き）
active_dict = dict(sorted(stock_suggestions.items()) if asset_type == "株式" else sorted(crypto_suggestions.items()))
display_names = [f"{k} ({v})" for k, v in active_dict.items()]
selected_display = st.selectbox("銘柄を選択", display_names)
symbol_input = active_dict[selected_display.split(" (")[0]]

# 期間選択（2つ）
period_options = {
    "1日": 1, "3日": 3, "1週間": 7, "1ヶ月": 30, "3ヶ月": 90, "6ヶ月": 180, "1年": 365
}
col1, col2 = st.columns(2)
with col1:
    period1 = st.selectbox("🕒 表示期間①", list(period_options.keys()), index=2)
with col2:
    period2 = st.selectbox("🕒 表示期間②", list(period_options.keys()), index=4)

# データ取得関数
def fetch_chart_data(symbol, days, asset_type):
    df = pd.DataFrame()
    if asset_type == "仮想通貨":
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "limit": days}
        res = requests.get(url, params=params)
        if res.status_code == 200:
            raw = res.json()
            df = pd.DataFrame(raw, columns=[
                "OpenTime", "Open", "High", "Low", "Close",
                "Volume", "CloseTime", "QuoteAssetVolume",
                "NumberOfTrades", "TakerBuyBase", "TakerBuyQuote", "Ignore"
            ])
            df["OpenTime"] = pd.to_datetime(df["OpenTime"], unit="ms")
            df.set_index("OpenTime", inplace=True)
            df = df[["Open", "High", "Low", "Close"]].astype(float)
    else:
        url = "https://api.twelvedata.com/time_series"
        params = {
            "symbol": symbol,
            "interval": "1day",
            "outputsize": days,
            "apikey": "7e5186e4a5c94e1a84c45bdefd0759cc",
            "format": "JSON"
        }
        res = requests.get(url, params=params)
        if res.status_code == 200 and "values" in res.json():
            raw = res.json()["values"]
            df = pd.DataFrame(raw)
            df["datetime"] = pd.to_datetime(df["datetime"])
            df.set_index("datetime", inplace=True)
            df = df.sort_index()
            df = df[["open", "high", "low", "close"]].astype(float)
            df.rename(columns={
                "open": "Open", "high": "High", "low": "Low", "close": "Close"
            }, inplace=True)
    return df

# チャート描画関数
def plot_chart(df, label):
    df["MA5"] = df["Close"].rolling(window=5).mean()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="green", decreasing_line_color="red",
        name="Candlestick"
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA5"], mode='lines', name="MA5", line=dict(color="blue")))
    fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], mode='lines', name="MA20", line=dict(color="orange")))
    fig.update_layout(
        title=label, dragmode='pan',
        xaxis=dict(fixedrange=False, showgrid=True),
        yaxis=dict(fixedrange=False, showgrid=True),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis_rangeslider_visible=False
    )
    return fig

# データ取得＆表示（左右）
col1, col2 = st.columns(2)
with col1:
    df1 = fetch_chart_data(symbol_input, period_options[period1], asset_type)
    if not df1.empty:
        fig1 = plot_chart(df1, f"{symbol_input.upper()} - {period1}")
        st.plotly_chart(fig1, use_container_width=True, config={"scrollZoom": True})

with col2:
    df2 = fetch_chart_data(symbol_input, period_options[period2], asset_type)
    if not df2.empty:
        fig2 = plot_chart(df2, f"{symbol_input.upper()} - {period2}")
        st.plotly_chart(fig2, use_container_width=True, config={"scrollZoom": True})
