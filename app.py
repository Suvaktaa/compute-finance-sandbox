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

# NEW: Fibonacci Toggle
show_fibo = st.sidebar.checkbox("Overlay Auto-Fibonacci Zones")

# New: Timeframe Selector (Added "1mo")
interval = st.sidebar.selectbox("Timeframe (Interval)", ["1mo", "1wk", "1d", "1h", "15m", "5m", "1m"])

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

# Command Center additions
days = st.sidebar.slider("Days of History", 45, max_days, min(60, max_days))

# Fetch Data
data = yf.download(ticker, period=f"{days}d", interval=interval)

if not data.empty:
    # --- THE NTP FIX: Convert UTC to IST ---
    if interval not in ["1d", "1wk", "1mo"]:
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

# ROW 1: Auto-Fibonacci Overlay
    if show_fibo:
        # 1. Identify the Swing High and Swing Low in the current data window
        swing_high = data['High'].max()
        swing_low = data['Low'].min()
        diff = swing_high - swing_low

        # 2. Calculate the standard Retracement Levels
        fibo_levels = {
            "0% (Swing High)": swing_high,
            "23.6%": swing_high - (diff * 0.236),
            "38.2%": swing_high - (diff * 0.382),
            "50.0% (Fair Value)": swing_high - (diff * 0.5),
            "61.8% (Golden Ratio)": swing_high - (diff * 0.618),
            "78.6%": swing_high - (diff * 0.786),
            "100% (Swing Low)": swing_low
        }

        # 3. Draw the zones on the chart
        for name, price in fibo_levels.items():
            # Emphasize the 61.8% Golden Ratio with a thicker, distinct line
            if "61.8%" in name:
                line_color = "gold"
                line_width = 2
                dash_style = "dash"
            else:
                line_color = "gray"
                line_width = 1
                dash_style = "dot"

            fig.add_hline(
                y=price, 
                line_dash=dash_style, 
                line_color=line_color, 
                line_width=line_width,
                opacity=0.7,
                annotation_text=f"{name}: {price:.2f}",
                annotation_position="top right",
                row=1, col=1
            )

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
    # FIX: Ensure both Daily (1d) and Monthly (1mo) bypass this filter
    if interval not in ["1d", "1wk", "1mo"]:
        fig.update_xaxes(rangebreaks=[
            dict(bounds=["sat", "mon"]), # hide weekends
            dict(bounds=[15.5, 9.25], pattern="hour") # hide hours outside NSE trading hours (3:30 PM to 9:15 AM)
        ])

    st.plotly_chart(fig, use_container_width=True)

else:
    st.error("Data fetch failed. API limit reached or network issue.")
