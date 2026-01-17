# 📊 Dashboard User Guide

## What's the Use of the Dashboard?

The dashboard is your **Command Center** - it's the human interface to the autonomous trading factory. Here's what it does for you:

### 🎯 **Primary Functions:**

1. **Risk Monitoring** 
   - See all bots' health at a glance
   - Spot underperformers before they hurt your account
   - Track portfolio-wide drawdown in real-time

2. **Performance Tracking**
   - Live equity curve shows if you're making or losing money
   - Individual bot PnL breakdown
   - Sharpe ratios for each strategy

3. **Quick Control**
   - One-click "Retire" button to kill underperforming bots
   - No need to dig through MT5 or stop Python processes manually
   - Filter by status (Paper/Live/Retired)

4. **Transparency**
   - Green heartbeat dots show which bots are actively running
   - Connection status tells you if the API is alive
   - See exactly which strategies are trading your money

### 🚦 **Why You Need It:**

**Without the Dashboard:**
- ❌ You'd have to open the database manually to see strategy stats
- ❌ Check MT5 to calculate total PnL across all magic numbers
- ❌ Guess which Python processes are which bots
- ❌ Trust that the "black box" is working

**With the Dashboard:**
- ✅ Instant visual proof the system is alive and trading
- ✅ Catch problems in seconds (connection loss, bad trades)
- ✅ Make data-driven decisions about which bots to promote to live
- ✅ Monitor from anywhere (could even expose it via a secure tunnel)

---

## 🖥️ **How to Access:**

Simply open your browser (Chrome, Edge, Firefox) and go to:
👉 **`http://localhost:5173/`**

The dashboard auto-refreshes every 5 seconds, so you can just leave it open on a second monitor.

---

## 📈 **What Each Section Shows:**

### **Top Cards (Fleet Overview)**
- **Total Strategies**: How many the factory has discovered
- **Live Trading**: Active bots with real money (green pulse = heartbeat)
- **Paper Trading**: Bots in simulation mode (yellow pulse)
- **Portfolio PnL**: Your total profit/loss across all bots
- **Avg Sharpe**: Average risk-adjusted return quality
- **Retired**: Auto-killed underperformers

### **Equity Curve Chart**
- Shows your cumulative profit over time
- If it's going up → the factory is working
- If it's flat → bots are being disciplined (waiting for good setups)
- If it's down → time to review which bots need retirement

### **Strategy Table**
- Each row = one bot
- **Heartbeat dots** = bot is alive and monitoring
- **Sharpe** in green = excellent quality (≥1.5)
- **PnL** in green = making money
- **Drawdown** in red = warning sign if >10%
- **Retire button** = manual override to kill a bot

---

## ⚙️ **When to Use It:**

- **Daily Check-In**: Morning coffee ritual - open the dashboard, scan for red flags
- **Before Going Live**: Watch paper bots for 24-48 hours to verify they trade
- **After Big News**: Check if volatility caused unexpected losses
- **Portfolio Rebalancing**: Decide which bot to promote from paper to live

---

## 🎨 **What's New (Just Upgraded):**

✅ **Heartbeat Indicators** - Pulsing green dots show active bots
✅ **Connection Status** - Top-right shows if API is connected
✅ **Error Handling** - Red banner appears if connection fails with retry button
✅ **Better States** - "No data yet" message while bots are starting
✅ **Animations** - Smooth transitions and hover effects
✅ **Footer Stats** - Quick glance at system health

**Bottom Line:** The dashboard turns the "invisible" autonomous system into something you can SEE, TRUST, and CONTROL. It's your "Mission Control" for the trading factory.
