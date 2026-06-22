import yfinance as yf
import torch
import pandas as pd
import numpy as np
import os
from rich.console import Console
from rich.table import Table

os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"
console = Console()

def get_sma_gpu(data, window, device):
    weights = torch.ones(1, 1, window, device=device) / window
    input_tensor = data.view(1, 1, -1)
    sma = torch.nn.functional.conv1d(input_tensor, weights, padding=0)
    return sma.view(-1)

def track_stocks():
    device = torch.device("cuda")
    # Tickers for Reliance and HDFC Bank
    stocks = {"Reliance": "RELIANCE.NS", "HDFC Bank": "HDFCBANK.NS"}
    
    table = Table(title="[bold yellow]Blue-Chip Momentum Tracker (GPU Accelerated)[/]")
    table.add_column("Stock", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("50-Day SMA", justify="right")
    table.add_column("200-Day SMA", justify="right")
    table.add_column("Trend", justify="center")

    for name, ticker in stocks.items():
        # Download recent 2 years (enough for 200 SMA)
        df = yf.download(ticker, period="2y", interval="1d", progress=False)
        
        # Handle yfinance multi-index (common in latest versions)
        if isinstance(df.columns, pd.MultiIndex):
            prices_raw = df['Close'][ticker]
        else:
            prices_raw = df['Close']
            
        prices = pd.to_numeric(prices_raw, errors='coerce').dropna().values.astype(np.float32)
        
        # GPU Calculation
        prices_gpu = torch.tensor(prices, device=device)
        sma50 = get_sma_gpu(prices_gpu, 50, device)[-1].item()
        sma200 = get_sma_gpu(prices_gpu, 200, device)[-1].item()
        current = prices[-1]

        trend = "[bold green]BULLISH[/]" if sma50 > sma200 else "[bold red]BEARISH[/]"
        
        table.add_row(name, f"₹{current:.2f}", f"₹{sma50:.2f}", f"₹{sma200:.2f}", trend)

    console.print(table)

if __name__ == "__main__":
    track_stocks()
