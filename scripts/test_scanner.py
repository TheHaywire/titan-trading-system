from titan_system.execution.main_loop import TitanBot
import logging

# Configure logging to be concise for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def test_scanner():
    print("\n" + "="*70)
    print("   TITAN INTELLIGENT SCANNER - LIVE DEMO")
    print("="*70 + "\n")
    
    # Use a smaller universe for speed in this demo
    universe = ["GOLD", "EURUSD", "BTCUSD"]
    bot = TitanBot(universe=universe)
    
    if bot.executor.connect():
        print(f"Connected. Scanning Market Universe: {universe}...\n")
        
        # We manually call scanner.scan() to get the list for display
        opportunities = bot.scanner.scan()
        
        print("\n" + "-"*70)
        print(f"{'SYMBOL':<10} | {'SCORE':<6} | {'SIGNAL':<8} | {'REASON':<40}")
        print("-" * 70)
        
        if not opportunities:
            print("No opportunities found (Choppy market or missing alignment).")
        else:
            for opp in opportunities:
                print(f"{opp['symbol']:<10} | {opp['score']:<6} | {opp['order_type']:<8} | {opp['comment']:<40}")
        
        print("-" * 70)
        
        if opportunities and opportunities[0]['score'] >= 80:
            print(f"\n[BEST] BEST OPPORTUNITY: {opportunities[0]['symbol']}!")
        else:
            print("\n[IDLE] No high-conviction trades (Score >= 80). Staying in cash.")
            
        print("\n" + "="*70)
        bot.executor.shutdown()
    else:
        print("❌ MT5 Connection Failed.")

if __name__ == "__main__":
    test_scanner()
