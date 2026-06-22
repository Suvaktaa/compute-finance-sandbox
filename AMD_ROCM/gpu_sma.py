import torch
import pandas as pd
import numpy as np
import os
import time

os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

def calculate_gpu_sma():
    if not torch.cuda.is_available():
        print("❌ GPU not found.")
        return

    device = torch.device("cuda")
    
    # Read CSV and handle the header issues
    # We use low_memory=False and skip the first few rows if they are junk
    df = pd.read_csv("nifty_50_10y.csv", header=[0, 1])
    
    # yfinance often creates a multi-index. We just want the 'Close' for '^NSEI'
    try:
        # Access the specific column in a multi-index
        prices_raw = df['Close']['^NSEI']
    except KeyError:
        # Fallback if your CSV saved differently
        df = pd.read_csv("nifty_50_10y.csv")
        prices_raw = df['Close']

    # Clean the data: Convert to numeric, drop any 'NaN' (missing values)
    prices_numeric = pd.to_numeric(prices_raw, errors='coerce').dropna()
    prices = prices_numeric.values.astype(np.float32)
    
    if len(prices) == 0:
        print("❌ No valid price data found in CSV.")
        return

    prices_gpu = torch.tensor(prices, device=device)
    
    def get_sma_gpu(data, window):
        weights = torch.ones(1, 1, window, device=device) / window
        input_tensor = data.view(1, 1, -1)
        sma = torch.nn.functional.conv1d(input_tensor, weights, padding=0)
        return sma.view(-1)

    print(f"🚀 Processing {len(prices)} days of Nifty 50 data...")
    
    start = time.time()
    sma50 = get_sma_gpu(prices_gpu, 50)
    sma200 = get_sma_gpu(prices_gpu, 200)
    torch.cuda.synchronize()
    end = time.time()

    print(f"✅ GPU Calculation complete in {((end-start)*1000):.4f}ms")
    
    last_sma50 = sma50[-1].item()
    last_sma200 = sma200[-1].item()
    
    print("-" * 30)
    print(f"Current Nifty Close: {prices[-1]:.2f}")
    print(f"50-Day SMA (GPU):    {last_sma50:.2f}")
    print(f"200-Day SMA (GPU):   {last_sma200:.2f}")
    
    if last_sma50 > last_sma200:
        print("📈 Trend: Bullish")
    else:
        print("📉 Trend: Bearish")

if __name__ == "__main__":
    calculate_gpu_sma()
