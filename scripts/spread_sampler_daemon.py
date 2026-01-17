"""
Background Spread Sampler
=========================
Runs continuously, sampling spreads every hour to build profiles.
Run this as a daemon: python scripts/spread_sampler_daemon.py
"""
import time
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.spread_profiler import add_spread_sample, print_spread_report

SAMPLE_INTERVAL_SECONDS = 3600  # 1 hour


def run_daemon():
    """Run continuous spread sampling."""
    print("=" * 60)
    print("SPREAD SAMPLER DAEMON STARTED")
    print(f"Sampling every {SAMPLE_INTERVAL_SECONDS // 60} minutes")
    print("=" * 60)
    
    sample_count = 0
    
    while True:
        try:
            sample = add_spread_sample()
            sample_count += 1
            
            if "error" not in sample:
                print(f"\n[Sample #{sample_count}] {sample['timestamp']}")
                print(f"  Hour: {sample['hour']}, Weekday: {sample['weekday']}")
                print(f"  Symbols sampled: {len(sample.get('spreads', {}))}")
                
                # Print top 5 tightest spreads
                if sample.get('spreads'):
                    sorted_spreads = sorted(sample['spreads'].items(), key=lambda x: x[1])[:5]
                    print("  Tightest spreads:", [f"{s[0]}:{s[1]}" for s in sorted_spreads])
            else:
                print(f"[ERROR] {sample['error']}")
            
            # Every 6 samples, print a mini report
            if sample_count % 6 == 0:
                print("\n--- INTERMEDIATE REPORT ---")
                print_spread_report(top_n=10)
            
        except Exception as e:
            print(f"[ERROR] Sampling failed: {e}")
        
        print(f"\nNext sample in {SAMPLE_INTERVAL_SECONDS // 60} minutes...")
        time.sleep(SAMPLE_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_daemon()
