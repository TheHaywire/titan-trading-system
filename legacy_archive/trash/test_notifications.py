"""
Test the autonomous trader notification system
Shows exactly what emails you'll receive when opportunities are found
"""
from autonomous_trader import AutonomousTrader
import datetime

print("=" * 80)
print("TESTING NOTIFICATION SYSTEM")
print("=" * 80)
print("\nThis will show you EXACTLY what happens when the bot finds opportunities:\n")

# Simulate finding 2 signals
test_signals = [
    {
        'symbol': 'EURUSD',
        'signal': 'BUY',
        'price': 1.05432,
        'sl': 1.05210,
        'tp': 1.05876,
        'atr': 0.00148
    },
    {
        'symbol': 'XAUUSD',
        'signal': 'SELL',
        'price': 2045.30,
        'sl': 2048.50,
        'tp': 2038.90,
        'atr': 2.13
    }
]

print("📊 SCENARIO: Bot just detected 2 signals at", datetime.datetime.now().strftime('%H:%M:%S'))
print("-" * 80)

for sig in test_signals:
    emoji = "🟢" if sig['signal'] == 'BUY' else "🔴"
    print(f"\n{emoji} {sig['symbol']} → {sig['signal']}")
    print(f"   Entry Price: {sig['price']}")
    print(f"   Stop Loss:   {sig['sl']} ({'⬇️' if sig['signal']=='BUY' else '⬆️'})")
    print(f"   Take Profit: {sig['tp']} ({'⬆️' if sig['signal']=='BUY' else '⬇️'})")
    print(f"   Risk/Reward: 1:2")

print("\n" + "=" * 80)
print("WHAT HAPPENS NEXT:")
print("=" * 80)

print("""
1. ⚡ INSTANT ACTION (Within seconds):
   - Bot executes both trades on your MT5 account
   - Positions are opened automatically
   - SL and TP are set

2. 📧 EMAIL ALERT (Within 10 seconds):
   - Subject: "⚡ 2 Signal(s) Detected & Executed"
   - Contains trade details (see email_preview.html)
   - Sent to: manankharbanda99@gmail.com

3. 📱 YOU ARE NOTIFIED:
   - Check your email
   - See trade confirmation
   - No action needed (already executed)

4. 🔄 MONITORING CONTINUES:
   - Bot watches the positions
   - If SL/TP hit, you get another email
   - Next scan happens in 15 minutes
""")

print("\n" + "=" * 80)
print("SENDING TEST EMAIL NOW...")
print("=" * 80)

# Actually send the test email
trader = AutonomousTrader()
trader.send_instant_alert(test_signals)

print("\n✅ TEST EMAIL SENT!")
print("📧 Check your inbox: manankharbanda99@gmail.com")
print("\nThis is EXACTLY what you'll receive every time the bot finds a signal.\n")
