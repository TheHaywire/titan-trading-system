from titan_system.execution.main_loop import TitanBot
import logging

# Configure simple logging to console for the demo
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def demo_run():
    print("\n" + "="*50)
    print("   TITAN SYSTEM | LIVE DEMO RUN")
    print("="*50 + "\n")
    print("Initializing Bot linked to MT5...")
    bot = TitanBot(universe=["GOLD"])
    
    if bot.executor.connect():
        print("\n[Action] Running ONE analysis cycle now...\n")
        bot.run_cycle()
        print("\n" + "="*50)
        print("✅ DEMO COMPLETE. The bot saw the market and made a decision.")
        print("Now launch 'start_bot.bat' to keep doing this 24/7.")
        print("="*50)
        bot.executor.shutdown()
    else:
        print("❌ Could not connect to MT5. Is it open?")

if __name__ == "__main__":
    demo_run()
