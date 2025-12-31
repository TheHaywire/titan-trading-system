
from titan_system.core.recon import MarketRecon
import logging

logging.basicConfig(level=logging.INFO)

def main():
    print("---------------------------------------")
    print("      TITAN ASSET RANKING              ")
    print("---------------------------------------")
    
    recon = MarketRecon()
    
    if not recon.connect():
        print("❌ Failed to connect to MT5.")
        return

    # Skip scan, just rank
    recon.rank_prime_assets()
    
    print("---------------------------------------")
    print("✅ Ranking Complete.")

if __name__ == "__main__":
    main()
