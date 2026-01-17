"""
Economic Calendar & News Integration
=====================================
Uses finvizfinance to get:
1. Economic calendar events (NFP, FOMC, CPI, etc.)
2. Market news headlines

Pre-trade filter: Skip trading around high-impact events
"""
from finvizfinance.calendar import Calendar
from finvizfinance.news import News
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# High-impact events and their trading blackout windows (minutes before/after)
HIGH_IMPACT_EVENTS = {
    "Nonfarm Payrolls": (30, 30),
    "NFP": (30, 30),
    "FOMC": (60, 60),
    "Federal Funds Rate": (60, 60),
    "CPI": (15, 15),
    "Core CPI": (15, 15),
    "PPI": (15, 15),
    "GDP": (15, 15),
    "Retail Sales": (10, 10),
    "Unemployment": (15, 15),
    "PMI": (10, 10),
    "ISM": (10, 10),
    "Consumer Confidence": (10, 10),
    "Interest Rate": (60, 60),
}


class EconomicCalendar:
    """Economic calendar for trading filters."""
    
    def __init__(self):
        self.calendar_data = None
        self.news_data = None
        self.last_refresh = None
        
    def refresh_calendar(self) -> pd.DataFrame:
        """Fetch latest economic calendar from Finviz."""
        try:
            cal = Calendar()
            self.calendar_data = cal.calendar()
            self.last_refresh = datetime.now()
            return self.calendar_data
        except Exception as e:
            print(f"Calendar fetch error: {e}")
            return pd.DataFrame()
    
    def refresh_news(self) -> Dict:
        """Fetch latest market news from Finviz."""
        try:
            news = News()
            self.news_data = news.get_news()
            return self.news_data
        except Exception as e:
            print(f"News fetch error: {e}")
            return {"news": [], "blogs": []}
    
    def get_upcoming_events(self, hours_ahead: int = 24) -> List[Dict]:
        """Get economic events in the next N hours."""
        if self.calendar_data is None or self.calendar_data.empty:
            self.refresh_calendar()
        
        if self.calendar_data is None or self.calendar_data.empty:
            return []
        
        # Parse and filter events
        events = []
        now = datetime.now()
        
        for _, row in self.calendar_data.iterrows():
            try:
                event_info = {
                    "date": row.get("Date", ""),
                    "time": row.get("Time", ""),
                    "event": row.get("Release", row.get("Event", "")),
                    "impact": self._get_event_impact(row.get("Release", row.get("Event", ""))),
                    "actual": row.get("Actual", ""),
                    "expected": row.get("Expected", ""),
                    "prior": row.get("Prior", ""),
                }
                events.append(event_info)
            except Exception:
                continue
        
        return events
    
    def _get_event_impact(self, event_name: str) -> str:
        """Determine impact level of an event."""
        if not event_name:
            return "LOW"
        
        event_upper = event_name.upper()
        
        # High impact keywords
        high_impact = ["NFP", "FOMC", "CPI", "GDP", "RATE", "PAYROLL", "EMPLOYMENT"]
        if any(kw in event_upper for kw in high_impact):
            return "HIGH"
        
        # Medium impact keywords
        medium_impact = ["PMI", "RETAIL", "HOUSING", "CONFIDENCE", "ISM"]
        if any(kw in event_upper for kw in medium_impact):
            return "MEDIUM"
        
        return "LOW"
    
    def is_safe_to_trade(self, symbol: str = None) -> Dict:
        """
        Check if it's safe to trade right now.
        Returns dict with verdict and reasoning.
        """
        result = {
            "safe": True,
            "reason": "No blocking events",
            "upcoming_events": [],
            "news_sentiment": "NEUTRAL"
        }
        
        events = self.get_upcoming_events(hours_ahead=2)
        
        # Check for high-impact events
        high_impact_soon = [e for e in events if e["impact"] == "HIGH"]
        
        if high_impact_soon:
            result["safe"] = False
            result["reason"] = f"High-impact event: {high_impact_soon[0]['event']}"
            result["upcoming_events"] = high_impact_soon
        
        return result
    
    def get_latest_news(self, limit: int = 10) -> List[Dict]:
        """Get latest market news headlines."""
        if self.news_data is None:
            self.refresh_news()
        
        if not self.news_data:
            return []
        
        news_list = self.news_data.get("news", [])
        
        # Format news items
        formatted = []
        for item in news_list[:limit]:
            if isinstance(item, dict):
                formatted.append(item)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                formatted.append({
                    "time": item[0] if len(item) > 0 else "",
                    "title": item[1] if len(item) > 1 else "",
                    "link": item[2] if len(item) > 2 else "",
                })
        
        return formatted
    
    def print_calendar_summary(self):
        """Print calendar and news summary."""
        print("\n" + "=" * 60)
        print("ECONOMIC CALENDAR & NEWS SUMMARY")
        print("=" * 60)
        
        # Trading safety check
        safety = self.is_safe_to_trade()
        if safety["safe"]:
            print("\n[SAFE] OK to trade - no blocking events")
        else:
            print(f"\n[CAUTION] {safety['reason']}")
        
        # Upcoming events
        events = self.get_upcoming_events(hours_ahead=24)
        if events:
            print(f"\n--- Upcoming Events ({len(events)}) ---")
            for e in events[:10]:
                impact = e.get("impact", "?")
                icon = "!!" if impact == "HIGH" else "!" if impact == "MEDIUM" else " "
                print(f"  {icon} {e.get('time', '??:??')} | {e.get('event', 'Unknown')[:40]} | {impact}")
        else:
            print("\n--- No upcoming events found ---")
        
        # Latest news
        news = self.get_latest_news(limit=5)
        if news:
            print(f"\n--- Latest News ---")
            for n in news:
                title = n.get("title", n.get(1, "No title"))
                if isinstance(title, str):
                    print(f"  - {title[:60]}...")
        else:
            print("\n--- No news available ---")


def pre_trade_check() -> Dict:
    """
    Quick pre-trade check function.
    Call before placing any trade.
    """
    cal = EconomicCalendar()
    return cal.is_safe_to_trade()


if __name__ == "__main__":
    cal = EconomicCalendar()
    cal.print_calendar_summary()
    
    print("\n--- Pre-Trade Check ---")
    result = pre_trade_check()
    print(f"Safe to trade: {result['safe']}")
    print(f"Reason: {result['reason']}")
