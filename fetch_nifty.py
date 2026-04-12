import yfinance as yf
import pandas as pd
import logging
import sys

# 1. Configure Enterprise Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] MARKET_PULL: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout) # Ensures cron's >> operator still catches the output
    ]
)

def fetch_data():
    logging.info("Initializing data pull from Yahoo Finance...")
    
    # Define your assets
    assets = {
        "Nifty_50": "^NSEI",
        "Bank_Nifty": "^NSEBANK"
    }
    
    for name, ticker in assets.items():
        logging.info(f"Downloading 10 years of data for {name} ({ticker})...")
        
        try:
            # Download the data
            df = yf.download(ticker, period="10y", interval="1d", progress=False)
            
            if not df.empty:
                # Handle yfinance's multi-index column format
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                    
                filename = f"{name.lower()}_10y.csv"
                df.to_csv(filename)
                logging.info(f"Saved {len(df)} rows to {filename}")
            else:
                logging.warning(f"No data returned for {name}.")
                
        except Exception as e:
            # This acts like a critical syslog alert if the API fails
            logging.error(f"Failed to download {name}: {str(e)}")

if __name__ == "__main__":
    fetch_data()
