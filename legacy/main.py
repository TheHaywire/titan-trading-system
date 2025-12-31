# ... (imports)
import time
import MetaTrader5 as mt5
import logging
from mt5_interface import MT5Interface
from strategy import Strategy
from notification import EmailNotification
from market_scanner import MarketScanner
import config

# Global Settings
TIMEFRAME = mt5.TIMEFRAME_H1
VOLUME = 0.01

# Setup Logging
logging.basicConfig(
    filename='trading_bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

def main():
    logging.info("Starting Trading Bot...")
    

    # Initialize Modules
    mt5_interface = MT5Interface()
    notifier = EmailNotification()
    scanner = MarketScanner()
    
    # Run Daily Analysis at Startup
    # This ensures the user gets a report every time they restart the bot, 
    # and allows us to test it immediately.
    try:
        from daily_analyst import DailyAnalyst
        daily_bot = DailyAnalyst()
        daily_bot.run_daily_analysis()
    except Exception as e:
        logging.error(f"Failed to run daily analysis: {e}")

    # Connect
    if not mt5_interface.start():
        logging.error("Failed to connect initialization")
        return

    # 1. Scan for Symbols
    logging.info("Scanning for tradable symbols...")
    # Using specific criteria for scan
    symbol_list = scanner.get_tradable_symbols(max_spread=30) 
    
    # Fallback if scan fails
    if not symbol_list:
        logging.warning("Scanner returned no symbols. Defaulting to Majors.")
        symbol_list = ["EURUSD", "GBPUSD", "USDJPY"]
    
    logging.info(f"Monitoring {len(symbol_list)} symbols: {symbol_list[:5]}...")
    
    # Initialize Strategy for each? Or one strategy instance reused?
    # Strategy instance holds parameters. We can reuse it if it doesn't store symbol-specific state 
    # that persists across ticks in a way that breaks.
    # Our simple strategy just recalculates on DF. So one instance is fine OR new one per symbol.
    # Let's create a map if we need state, but for now single instance usage is cleaner if stateless.
    # Actually, Strategy init takes "symbol" but only assigns it. 
    # Let's make Strategy stateless regarding checking different dataframes.
    
    strategies = {s: Strategy(s, TIMEFRAME, short_window=30, long_window=100) for s in symbol_list}
    
    notifier.send_email("Bot Started", f"Bot started. Monitoring {len(symbol_list)} symbols.")

    try:
        while True:
            # We must ensure connection is alive before looping
            if not mt5_interface.connected:
                mt5_interface.start()

            for symbol in symbol_list:
                try:
                    # 1. Get Data
                    df = mt5_interface.get_closes(symbol, TIMEFRAME)
                    
                    if df is not None:
                        # 2. Check Strategy
                        strat = strategies[symbol]
                        signal = strat.generate_signal(df)
                        
                        if signal:
                            logging.info(f"[{symbol}] Signal detected: {signal}")
                            
                            # 3. Place Order
                            order_type = mt5.ORDER_TYPE_BUY if signal == 'BUY' else mt5.ORDER_TYPE_SELL
                            result = mt5_interface.place_market_order(symbol, VOLUME, order_type)
                            
                            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                                msg = f"Executed {signal} order for {symbol} at {result.price}"
                                logging.info(msg)
                                notifier.send_email(f"Trade Executed: {symbol}", msg)
                            else:
                                err_msg = f"Failed to execute {signal} order for {symbol}. Retcode: {result.retcode if result else 'None'}"
                                logging.error(err_msg)
                    
                    # Small sleep between symbols to not hammer CPU/API too hard?
                    # MT5 is fast, but let's be polite.
                    time.sleep(0.1)

                except Exception as e:
                    logging.error(f"Error processing {symbol}: {e}")
                    continue
            
            # Sleep after checking ALL symbols
            logging.info("Completed scan cycle. Sleeping...")
            time.sleep(60)

    except KeyboardInterrupt:
        logging.info("Stopping Bot...")
        mt5_interface.shutdown()
        logging.info("Bot Stopped.")

if __name__ == "__main__":
    main()
