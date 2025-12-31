from titan_system.execution.main_loop import TitanBot
import logging

# Mock the sleep to just run once
import time
def mock_sleep(seconds):
    print(f"(TEST) Would sleep for {seconds} seconds. Exiting test.")
    raise KeyboardInterrupt # Break loop

time.sleep = mock_sleep

def test_live_loop():
    print("Testing Live Loop (Simulation)...")
    
    bot = TitanBot(symbol="GOLD", timeframe="H1")
    
    # We want to verify it runs one cycle without crashing
    
    # Override run_cycle to confirm it's called? 
    # No, let's run the actual cycle but maybe mock executor.connect if we don't want real MT5 actions?
    # Actually, user has MT5, let's try to really connect (it just reads data), 
    # but maybe we should ensure it doesn't place a random trade if signal accidentally triggers?
    # The logic requires SMA crossover EXACTLY now. Unlikely.
    # But to be safe, we can mock execute_order.
    
    original_execute = bot.executor.execute_order
    
    def mock_execute(symbol, type, vol, **kwargs):
        print(f"✅ (MOCK) EXECUTED: {symbol} {type} {vol}")
        return {"retcode": 10009}
        
    bot.executor.execute_order = mock_execute
    
    print("Starting Bot...")
    bot.start()
    print("Test Complete.")

if __name__ == "__main__":
    test_live_loop()
