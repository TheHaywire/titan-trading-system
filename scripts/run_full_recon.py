
from titan_system.core.recon import MarketRecon
import time

def main():
    print("---------------------------------------")
    print("      TITAN MARKET RECONNAISSANCE      ")
    print("---------------------------------------")
    print("This will fetch ALL symbols from MT5 and rank them.")
    print("It may take 5-10 minutes depending on your broker.")
    print("---------------------------------------")
    
    recon = MarketRecon()
    
    if not recon.connect():
        print("❌ Failed to connect to MT5.")
        return

    start = time.time()
    
    # 1. Discovery
    recon.scan_universe()
    
    # 2. Analysis & Ranking
    recon.rank_prime_assets()
    
    elapsed = time.time() - start
    print(f"---------------------------------------")
    print(f"✅ DONE in {elapsed:.1f} seconds.")
    print("Check titan.db >> market_universe table.")
    print("---------------------------------------")

if __name__ == "__main__":
    main()
