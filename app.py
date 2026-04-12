import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# Hardware Handshake
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

st.set_page_config(layout="wide", page_title="Nagu's Pro Trading Terminal")
st.title("📈 NSE Intelligence Dashboard (4K Edition)")

# --- COMMAND CENTER ---
st.sidebar.header("Command Center")
ticker = st.sidebar.selectbox("Select Asset", ["^NSEI", "^NSEBANK", "RELIANCE.NS", "HDFCBANK.NS"])

# New: Timeframe Selector (Added "1mo")
interval = st.sidebar.selectbox("Timeframe (Interval)", ["1mo", "1d", "1h", "15m", "5m", "1m"])

# API Firewall: Protect against Yahoo's retention limits
if interval == "1m":
    max_days = 7
    st.sidebar.warning("API Limit: 1m data restricted to 7 days.")
elif interval in ["5m", "15m"]:
    max_days = 60
    st.sidebar.warning(f"API Limit: {interval} data restricted to 60 days.")
elif interval == "1h":
    max_days = 730
else:
    # This covers both "1d" an d "1mo"
    max_days = 3650 # 10 years limit

days = st.sidebar.slider("Days of History", 1, max_days, min(30, max_days))

# Fetch Data
data = yf.download(ticker, period=f"{days}d", interval=interval)

if not data.empty:
    # --- THE NTP FIX: Convert UTC to IST ---
    if interval not in ["1d", "1mo"]:
        # yfinance intraday data comes with a UTC timezone awareness
        if data.index.tz is not None:
            data.index = data.index.tz_convert('Asia/Kolkata')
        else:
            data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            
    # Flatten Multi-Index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

if not data.empty:
    # Flatten Multi-Index
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # Calculate Indicators
    data.ta.bbands(length=20, std=2, append=True)
    data.ta.rsi(length=14, append=True)
    data.ta.macd(fast=12, slow=26, signal=9, append=True)

    # Create the Subplot Grid
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.6, 0.2, 0.2])

    # ROW 1: Price Action
    fig.add_trace(go.Candlestick(
        x=data.index, open=data['Open'], high=data['High'], 
        low=data['Low'], close=data['Close'], name="Price"
    ), row=1, col=1)

    try:
        fig.add_trace(go.Scatter(x=data.index, y=data['BBU_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name="Upper BB"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['BBL_20_2.0'], line=dict(color='gray', width=1, dash='dot'), name="Lower BB"), row=1, col=1)
    except KeyError:
        pass

    # ROW 2: RSI
    try:
        fig.add_trace(go.Scatter(x=data.index, y=data['RSI_14'], line=dict(color='purple'), name="RSI"), row=2, col=1)
        fig.add_hline(y=70, line_dash="dot", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="green", row=2, col=1)
    except KeyError:
        pass

    # ROW 3: MACD
    try:
        fig.add_trace(go.Bar(x=data.index, y=data['MACDh_12_26_9'], name="MACD Hist", marker_color='gray'), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_12_26_9'], line=dict(color='blue'), name="MACD Line"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACDs_12_26_9'], line=dict(color='orange'), name="Signal Line"), row=3, col=1)
    except KeyError:
        pass

    fig.update_layout(
        height=1100, 
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=80, t=20, b=20),
        template="plotly_dark"
    )
    
    # 4K Optimization for intraday: Hide empty gaps (weekends/nights)
    if interval != "1d":
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]), # hide weekends
            dict(bounds=[15.5, 9.25], pattern="hour") # hide hours outside NSE trading hours (3:30 PM to 9:15 AM)
        ])

    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Data fetch failed. API limit reached or network issue.")
