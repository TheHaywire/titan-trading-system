"""
TITAN SYSTEM - INSTITUTIONAL CONFIGURATION
Broker: XM Global MT5 (Server 2)
Generated: 2026-01-01 via Deep Recon
"""

class TitanFuturesConfig:
    # --- BROKER CONSTANTS ---
    BROKER_NAME = "XMGlobal-MT5"
    LEVERAGE = 1000  # 1:1000
    
    # --- ASSET SPECIFICS (Overrides) ---
    # Used when MT5 info might be ambiguous or needs enforcement
    CONTRACT_SIZES = {
        "GOLD": 10,       # Custom: Standard is 100
        "XAUUSD": 10,
        "COCOA": 10,      # Verify in recon
        "US500": 1,       # Index CFDs often 1 or 10
    }
    
    # --- RISK LIMITS ---
    MAX_DAILY_LOSS_PCT = 5.0
    MAX_POSITION_RISK_PCT = 1.0  # 1% Account Risk per trade
    MAX_PORTFOLIO_RISK_PCT = 5.0 # Max correlated exposure
    
    # --- EXECUTION ---
    # Path to MT5 Terminal (auto-detected usually, but good to override)
    MT5_PATH = r"C:\Program Files\XM Global MT5\terminal64.exe"
    
    # --- FAT TAIL TARGETS ---
    # Validated Strategy Whitelist
    FAT_TAIL_SYMBOLS = [
        "Gold", "XAUUSD", "GOLD", # Handle aliases
        "Cocoa", "#Cocoa",
        "US500", "US500Cash",
        "Palladium"
    ]
    
    def __init__(self):
        # Allow env var overrides
        import os
        self.mt5_login = int(os.getenv("MT5_LOGIN", 0))
        self.mt5_password = os.getenv("MT5_PASSWORD", "")
        self.mt5_server = os.getenv("MT5_SERVER", "XMGlobal-MT5 2")
