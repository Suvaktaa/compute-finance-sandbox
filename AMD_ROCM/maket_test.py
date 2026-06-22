import torch
import time
import os

# The "Network Spoof" for your RX 6600
os.environ["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"

def run_trading_benchmark():
    if not torch.cuda.is_available():
        print("❌ Error: GPU not detected by PyTorch.")
        return

    device = torch.device("cuda")
    print(f"🚀 Benchmark started on: {torch.cuda.get_device_name(0)}")

    # Simulating a massive Correlation Matrix (15k x 15k)
    # This represents calculating dependencies for a huge basket of NSE stocks
    size = 15000 
    print(f"📊 Generating {size}x{size} Matrix in VRAM...")
    
    # Randomly generate mock stock price data
    a = torch.randn(size, size, device=device)
    b = torch.randn(size, size, device=device)

    print("⚡ Running 10 cycles of Matrix Multiplication...")
    start_time = time.time()
    
    for i in range(1, 11):
        # This is where your 1792 GPU cores do the heavy lifting
        result = torch.matmul(a, b)
        if i % 2 == 0:
            print(f"   Cycle {i} complete...")
    
    # Synchronize to ensure the "packets" are fully processed
    torch.cuda.synchronize()
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n✅ SUCCESS!")
    print(f"⏱️ Total processing time: {total_time:.4f} seconds")
    print(f"📉 This would take several minutes on a standard CPU.")

if __name__ == "__main__":
    run_trading_benchmark()
