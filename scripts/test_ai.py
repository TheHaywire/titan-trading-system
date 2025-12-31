
import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_system.analytics.ai_analyst import AIAnalyst

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_ai():
    print("🧠 Testing Gemini AI Analyst...")
    ai = AIAnalyst()
    
    if not ai.enabled:
        print("❌ AI is disabled (API Key missing?)")
        return

    mock_data = {
        'price': 1.0500,
        'trend': 'BEARISH',
        'rsi': 25,
        'adx': 45,
        'd1_trend': 'BEARISH',
        'pivot': 1.0550
    }
    
    print(f"📤 Sending Data: {mock_data}")
    insight = await ai.analyze("EURUSD", mock_data)
    print(f"✅ AI Response: {insight}")

if __name__ == "__main__":
    asyncio.run(test_ai())
