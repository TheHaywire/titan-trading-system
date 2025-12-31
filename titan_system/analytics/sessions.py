
import datetime
from typing import List, Dict

class SessionManager:
    """
    Manages global market sessions and recommends assets based on liquidity.
    """
    
    # Session Schedule (Approximate UTC)
    # Start and End hours are inclusive/exclusive logic usually, but here we cover the core hours.
    SESSIONS = {
        "ASIAN": {
            "start": 22, # 10 PM UTC (Sydney open)
            "end": 8,    # 8 AM UTC (Tokyo close overlap)
            "focus": ["USDJPY", "AUDUSD", "NZDUSD", "AUDJPY", "GBPJPY"]
        },
        "LONDON": {
            "start": 7,  # 7 AM UTC (Frankfurt open)
            "end": 16,   # 4 PM UTC (London close)
            "focus": ["EURUSD", "GBPUSD", "EURGBP", "USDCHF", "GBPJPY", "EURJPY"]
        },
        "NEW_YORK": {
            "start": 12, # 12 PM UTC (Pre-market)
            "end": 21,   # 9 PM UTC (Close)
            "focus": ["EURUSD", "GBPUSD", "USDCAD", "XAUUSD", "BTCUSD", "USDCHF"]
        }
    }

    @staticmethod
    def get_market_status(target_time: datetime.datetime = None) -> Dict:
        """
        Returns the current active sessions and a list of high-liquidity symbols.
        """
        if target_time is None:
            target_time = datetime.datetime.utcnow()
            
        current_hour = target_time.hour
        
        active_sessions = []
        focus_list = set()
        
        for name, data in SessionManager.SESSIONS.items():
            start = data["start"]
            end = data["end"]
            
            # Handle crossover midnight (e.g. Asian session 22:00 -> 08:00)
            if start > end:
                if current_hour >= start or current_hour < end:
                    active_sessions.append(name)
                    focus_list.update(data["focus"])
            else:
                if start <= current_hour < end:
                    active_sessions.append(name)
                    focus_list.update(data["focus"])
                    
        return {
            "utc_time": target_time.strftime("%H:%M"),
            "active_sessions": active_sessions, # e.g. ["LONDON", "NEW_YORK"]
            "liquidity_tier": "HIGH" if len(active_sessions) >= 2 else "MODERATE" if active_sessions else "LOW",
            "recommended_symbols": list(focus_list)
        }

    @staticmethod
    def is_symbol_active(symbol: str) -> bool:
        """
        Checks if a symbol is in the recommended list for the current time.
        """
        status = SessionManager.get_market_status()
        # If no session is active (rare), everything is risky, but let's default to False
        if not status["active_sessions"]:
            return False
            
        return symbol in status["recommended_symbols"]
