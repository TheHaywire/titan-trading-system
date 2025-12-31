
import datetime
import logging

logger = logging.getLogger("Titan.News")

class NewsFilter:
    """
    Manages Economic Calendar and Risk Events.
    Currently maps common 'Volatile Times' for major currencies.
    Future: Integrate with FinancialModelingPrep or ForexFactory API.
    """
    
    # Static "Red Folder" times (UTC)
    # These are illustrative of typical major release windows
    DANGER_ZONES = [
        (13, 30), # US CPI / NFP / GDP (13:30 UTC)
        (14, 00), # FOMC / Fed Speak
        (19, 00), # FOMC Minutes
        (12, 45), # ECB Rates
        (13, 15), # ECB Press Conf
    ]

    def check_risk(self, symbol: str) -> dict:
        """
        Returns risk status for a symbol.
        { 'risk_level': 'LOW'|'HIGH', 'message': ... }
        """
        now = datetime.datetime.utcnow()
        
        # 1. Check Hardcoded Danger Zones (Window: +/- 15 mins)
        for h, m in self.DANGER_ZONES:
            event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = abs((now - event_time).total_seconds())
            
            if diff < 900: # 15 minutes
                return {
                    "risk_level": "HIGH",
                    "source": "Session",
                    "message": f"High Volatility Window ({h}:{m:02d} UTC)"
                }

        # 2. Check Session Open Volatility (London 08:00, NY 13:00)
        # Often messy price action at opens.
        # Let's say we avoid first 5 mins of London/NY.
        if (now.hour == 8 and now.minute < 5) or (now.hour == 13 and now.minute < 5):
             return {
                    "risk_level": "MEDIUM",
                    "source": "Session",
                    "message": "Market Open Volatility"
                }

        return {
            "risk_level": "LOW",
            "source": "Clean",
            "message": "No News Detected"
        }
