
from datetime import datetime, time
import pytz

class SessionManager:
    """
    Manages trading sessions to optimize timing.
    """
    
    # GMT Times
    LONDON_OPEN = time(8, 0)
    LONDON_CLOSE = time(16, 0)
    NY_OPEN = time(13, 0)
    NY_CLOSE = time(21, 0)
    
    # Asian Dead Zone (Usually 21:00 GMT - 06:00 GMT)
    ASIAN_START = time(21, 0)
    ASIAN_END = time(6, 0)

    # INSTITUTIONAL FORENSIC DATA: Hour 19 is the "Death Zone" (-$2.5M loss)
    DEATH_ZONE_START = time(18, 0)
    DEATH_ZONE_END = time(21, 0)

    # INSTITUTIONAL FORENSIC DATA: Hour 13 is the "Power Hour" (+$1M profit)
    GOLDEN_HOUR_START = time(12, 0)
    GOLDEN_HOUR_END = time(15, 0)
    
    def __init__(self):
        self.timezone = pytz.utc
        
    def get_session(self) -> dict:
        """Returns current session info."""
        now = datetime.now(self.timezone).time()
        
        # Check Death Zone First (Highest Priority)
        is_death_zone = self.DEATH_ZONE_START <= now <= self.DEATH_ZONE_END
        
        # Check Power Hour
        is_golden_hour = self.GOLDEN_HOUR_START <= now <= self.GOLDEN_HOUR_END
        
        # Check Standard Sessions
        is_london = self.LONDON_OPEN <= now <= self.LONDON_CLOSE
        is_ny = self.NY_OPEN <= now <= self.NY_CLOSE
        
        # Check Asian / Low Volatility
        is_asian = (now >= self.ASIAN_START) or (now <= self.ASIAN_END)
        
        # Logic
        status = "NEUTRAL"
        can_trade = True
        multiplier = 1.0
        
        if is_death_zone:
            status = "💀 DEATH_ZONE_LOCKED"
            can_trade = False
            multiplier = 0.0
        elif is_golden_hour:
            status = "🚀 POWER_HOUR_ACTIVE"
            multiplier = 1.5 
        elif is_london or is_ny:
            status = "ACTIVE_SESSION"
            multiplier = 1.0
        elif is_asian:
            status = "ASIAN_SESSION"
            can_trade = False 
            multiplier = 0.0
            
        return {
            "status": status,
            "london": is_london,
            "ny": is_ny,
            "asian": is_asian,
            "is_death_zone": is_death_zone,
            "can_trade_majors": can_trade,
            "risk_multiplier": multiplier
        }
