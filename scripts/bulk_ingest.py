from titan_system.data.ingest_mt5 import ingest_history
from titan_system.research.auditor import TitanAuditor
import logging
import MetaTrader5 as mt5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Titan.Ingest")

def ingest_all():
    if not mt5.initialize():
        print("MT5 Init failed")
        return
        
    universe = [
        "GOLD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", # FX
        "BTCUSD", "ETHUSD", "SOLUSD", "MATICUSD", # Crypto
        "US500", "US30", "USTEC", "GER40", # Indices
        "WTI" # Commodities
    ]
    
    days_back = 180
    print(f"🚀 Ingesting {days_back} days of history for {len(universe)} symbols...")
    
    for raw in universe:
        try:
            auditor = TitanAuditor(raw)
            symbol = auditor.symbol
            print(f"  Ingesting {symbol}...")
            ingest_history(symbol, "H4", days=days_back)
            ingest_history(symbol, "H1", days=days_back)
        except Exception as e:
            print(f"  Error on {raw}: {e}")
            
    mt5.shutdown()
    print("✅ Ingestion Complete.")

if __name__ == "__main__":
    ingest_all()
