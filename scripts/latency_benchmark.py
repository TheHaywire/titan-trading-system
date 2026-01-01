"""
IPC Latency Benchmark (EPIC-02)
Measures the round-trip time (RTT) between the Python engine and MT5 Terminal.
Crucial for institutional-grade execution speed validation.
"""

import MetaTrader5 as mt5
import time
import numpy as np

def run_benchmark(iterations=100):
    if not mt5.initialize():
        print("❌ MT5 Initialization Failed")
        return

    print(f"🛰️ Benchmarking IPC Latency ({iterations} iterations)...")
    
    latencies = []
    
    for i in range(iterations):
        start = time.perf_counter()
        # Use a lightweight call like account_info or terminal_info
        _ = mt5.account_info()
        end = time.perf_counter()
        
        latencies.append((end - start) * 1000)
        
        if (i+1) % 20 == 0:
            print(f" - Progress: {i+1}/{iterations}...")

    mt5.shutdown()
    
    avg_lat = np.mean(latencies)
    min_lat = np.min(latencies)
    max_lat = np.max(latencies)
    std_lat = np.std(latencies)
    p95_lat = np.percentile(latencies, 95)

    print("\n📊 [LATENCY RESULTS]")
    print(f"- Average RTT: {avg_lat:.3f} ms")
    print(f"- Minimum RTT: {min_lat:.3f} ms")
    print(f"- Maximum RTT: {max_lat:.3f} ms")
    print(f"- P95 Latency: {p95_lat:.3f} ms")
    print(f"- Std Deviation: {std_lat:.3f} ms")

    target = 50.0
    if avg_lat < target:
        print(f"\n✅ SUCCESS: Average latency ({avg_lat:.2f}ms) is within Institutional Target (<{target}ms).")
    else:
        print(f"\n⚠️ WARNING: Average latency ({avg_lat:.2f}ms) EXCEEDS Institutional Target (<{target}ms). Check CPU/RAM load.")

if __name__ == "__main__":
    run_benchmark()
