
import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from titan_system.notifications.telegram_bot import TelegramNotifier

logging.basicConfig(level=logging.INFO)

async def test_telegram():
    print("📱 Testing Telegram Bot...")
    tg = TelegramNotifier()
    
    if not tg.enabled:
        print("❌ Telegram disabled.")
        return
        
    print("📤 Sending Test Message...")
    await tg.send_message("Greetings from Titan System Phase 4! 🚀", priority="HIGH")
    
    print("📤 Sending Mock Trade Alert...")
    mock_trade = {'symbol': 'EURUSD', 'type': 'BUY', 'price': 1.0550}
    mock_analysis = {'score': 85, 'ai_insight': 'Bias: BULLISH. Strong momentum breakout.'}
    
    await tg.send_trade_alert(mock_trade, mock_analysis)
    print("✅ Done.")

if __name__ == "__main__":
    asyncio.run(test_telegram())
