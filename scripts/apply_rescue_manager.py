
import MetaTrader5 as mt5
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Titan.RescueManager")

def apply_rescue_plan(symbol="GOLD", sl=4169.76, tp=4239.31):
    if not mt5.initialize():
        logger.error("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        logger.info(f"No positions found for {symbol}")
        return

    logger.info(f"Applying Rescue Logic to {len(positions)} positions for {symbol}...")
    logger.info(f"Targets >> SL: {sl} | TP: {tp}")
    
    for pos in positions:
        # Update Request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": pos.ticket,
            "symbol": symbol,
            "sl": float(sl),
            "tp": float(tp)
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
             logger.error(f"Failed to update positions {pos.ticket}: {result.comment} ({result.retcode})")
        else:
             logger.info(f"✅ Secured position {pos.ticket}")

    mt5.shutdown()

if __name__ == "__main__":
    # Levels from find_levels.py
    apply_rescue_plan("GOLD", sl=4169.76, tp=4239.31)
