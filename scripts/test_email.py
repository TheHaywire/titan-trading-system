
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_system.notifications.email import EmailNotifier

# Mock stats for testing
mock_stats = {
    'total_profit': 150.50,
    'trades_count': 5,
    'win_rate': 80.0,
    'balance': 10150.50,
    'equity': 10150.50
}

mock_trade = {
    'symbol': 'EURUSD',
    'type': 'BUY',
    'price': 1.0500,
    'comment': 'Titan-Test'
}

def test_email():
    print("📧 Testing Titan Notification System...")
    notifier = EmailNotifier()
    
    print("\n1. Sending Trade Alert...")
    notifier.send_trade_alert(mock_trade)
    
    print("\n2. Sending Daily Report...")
    notifier.send_daily_report(mock_stats)
    
    print("\n✅ Test Requests Sent! Check your inbox.")

if __name__ == "__main__":
    test_email()
