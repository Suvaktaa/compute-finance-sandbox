# Compute Finance Sandbox

A hardware-accelerated development sandbox combining high-throughput financial data pipelines with an optimized AMD ROCm GPU compute framework on Arch Linux.

## 📂 Project Architecture Layout
├── AMD_ROCM/
│   ├── gpu_sma.py             # System management tracker for AMD GPU compute
│   └── maket_test.py          # Parallel matrix multiplication stress-testing simulation
├── Finance/
│   ├── app.py                 # Core Streamlit portal application
│   ├── nifty_dashboard.py     # Strategy analytics implementation engine
│   ├── fetch_nifty.py         # Daily automation data fetch utility (yfinance API)
│   ├── *.csv                  # Historical index datasets
│   └── log/
│       └── market_pull.log    # Pipeline data extraction runtime logs
├── .gitignore                 # Home directory tracking safety rules
└── README.md                  # This document

## 🚀 Execution & Quick Start

### 1. Pre-requisites & Workspace Activation
Ensure your user space virtual environment is active before running calculations or visualizers:
```bash
source ~/ai_env/bin/activate

