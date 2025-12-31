
import os
from dotenv import load_dotenv

# Try loading .env if it exists
load_dotenv()

class Config:
    # Project Settings
    PROJECT_NAME = "Titan Trading System"
    VERSION = "2.0.0 (YC Revamp)"
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DB_PATH = os.path.join(BASE_DIR, "titan.db")
    
    # MetaTrader 5
    MT5_LOGIN = int(os.getenv("MT5_LOGIN", 0))
    MT5_PASSWORD = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER = os.getenv("MT5_SERVER", "")
    MT5_PATH = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5")

    # Risk Management
    MAX_DAILY_DRAWDOWN_PERCENT = 5.0
    MAX_SYMBOL_EXPOSURE_LOTS = 2.0
    MAX_CORRELATION_THRESHOLD = 0.8
    
    # Strategy
    TIMEFRAMES = ["M15", "H1", "H4"]
    TRADING_SYMBOLS = [
        "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "US30", "BTCUSD"
    ]
    ADX_THRESHOLD = 25
    
    # API
    API_HOST = "0.0.0.0"
    API_PORT = 8000
    
    @classmethod
    def show_config(cls):
        print(f"🔧 Configuration Loaded: {cls.PROJECT_NAME} v{cls.VERSION}")
        print(f"📂 Database: {cls.DB_PATH}")

