import torch
import pandas as pd
import numpy as np
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Hardware Handshake
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"
console = Console()

def get_sma_gpu(data, window, device):
    weights = torch.ones(1, 1, window, device=device) / window
    input_tensor = data.view(1, 1, -1)
    sma = torch.nn.functional.conv1d(input_tensor, weights, padding=0)
    return sma.view(-1)

def show_dashboard():
    device = torch.device("cuda")
    df = pd.read_csv("nifty_50_10y.csv", header=[0,1])
    prices_raw = df['Close']['^NSEI']
    prices_numeric = pd.to_numeric(prices_raw, errors='coerce').dropna()
    prices = prices_numeric.values.astype(np.float32)
    
    # Move to GPU
    prices_gpu = torch.tensor(prices, device=device)
    sma50 = get_sma_gpu(prices_gpu, 50, device)[-1].item()
    sma200 = get_sma_gpu(prices_gpu, 200, device)[-1].item()
    current = prices[-1]

    # Create a Rich Table
    table = Table(title="[bold cyan]NSE Market Intelligence Dashboard[/]", show_header=True, header_style="bold magenta")
    table.add_column("Indicator", style="dim")
    table.add_column("Value", justify="right")
    table.add_column("Status", justify="center")

    trend = "[bold green]BULLISH[/]" if sma50 > sma200 else "[bold red]BEARISH[/]"
    
    table.add_row("Current Nifty Close", f"₹{current:,.2f}", "---")
    table.add_row("50-Day SMA (Fast)", f"₹{sma50:,.2f}", "[yellow]Support[/]" if current > sma50 else "[red]Resistance[/]")
    table.add_row("200-Day SMA (Slow)", f"₹{sma200:,.2f}", "[blue]Long Term[/]")
    table.add_row("[bold]Market Trend[/]", "---", trend)

    console.print(Panel(table, expand=False, border_style="blue"))

if __name__ == "__main__":
    show_dashboard()
