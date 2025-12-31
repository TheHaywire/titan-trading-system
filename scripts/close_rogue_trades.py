
import MetaTrader5 as mt5
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Titan.RiskManager")

def close_positions_by_symbol(symbol: str):
    if not mt5.initialize():
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        logger.info(f"No positions found for {symbol}")
        return

    logger.info(f"Closing {len(positions)} positions for {symbol}...")
    
    for pos in positions:
        # Close Request
        type_close = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if type_close == mt5.ORDER_TYPE_SELL else mt5.symbol_info_tick(symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": symbol,
            "volume": pos.volume,
            "type": type_close,
            "price": price,
            "slippage": 10,
            "magic": pos.magic,
            "comment": "Emergency Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
             logger.error(f"Failed to close position {pos.ticket}: {result.comment}")
        else:
             logger.info(f"Closed position {pos.ticket}")

    mt5.shutdown()

if __name__ == "__main__":
    close_positions_by_symbol("GOLD")
