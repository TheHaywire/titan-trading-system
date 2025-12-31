
import MetaTrader5 as mt5
from datetime import datetime
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import settings

def test_calendar():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    # Login
    mt5.login(login=settings.mt5_login, password=settings.mt5_password, server=settings.mt5_server)

    print("Checking Economic Calendar...")
    try:
        # Get events for this week
        now = datetime.now()
        events = mt5.calendar_value(now, now)
        if events:
            print(f"Found {len(events)} events today.")
        else:
            print("No events found via mt5.calendar_value (might not be supported by broker).")
            
    except Exception as e:
        print(f"Error accessing calendar: {e}")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_calendar()
