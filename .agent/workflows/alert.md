---
description: Set price alerts for key levels and trade setups
---

# Smart Alert System

Monitor markets 24/7 and get notified when important conditions are met (price levels, patterns, setups forming).

## Usage

```
/alert [SYMBOL] [CONDITION] [LEVEL]
```

**Examples:**
- `/alert GOLD above 4500` - Alert when Gold breaks above 4500
- `/alert BTCUSD below 90000` - Alert when Bitcoin drops below 90k
- `/alert GOLD setup 7+` - Alert when 7+/10 quality setup forms
- `/alert EURUSD divergence` - Alert on divergence detection

## What It Does

Monitor and alert on:

✅ **Price Levels** - Breakout/breakdown alerts
✅ **Support/Resistance Tests** - Price approaches key levels
✅ **Pattern Formation** - Divergence, triangles, flags formed
✅ **Setup Quality** - High-quality setups appear (7+/10)
✅ **Confluence Zones** - Price enters confluence area
✅ **RSI Extremes** - Overbought/oversold conditions
✅ **Volatility Spikes** - Unusual price movement
✅ **Session Opens** - London/NY session starting

## How to Run

// turbo
1. Start the alert monitor
```bash
python scripts/alert_monitor.py
```

This runs in background and sends notifications via:
- Desktop notifications (Windows toast)
- Telegram messages
- Email (if configured)
- Sound alerts

## Alert Types

### Price Alerts
```
GOLD breaks above 4500.00
→ Notification: "🚨 GOLD breakout! Now at 4503.50"
```

### Setup Alerts
```
7+/10 setup detected on BTCUSD
→ Notification: "⭐ Premium setup on BTCUSD - 8.2/10 score"
```

### Pattern Alerts
```
Bearish divergence formed on EURUSD 1H
→ Notification: "📉 Divergence alert: EURUSD showing weakness"
```

## Configuration

Edit `config/alerts.json`:
```json
{
  "telegram_bot_token": "YOUR_TOKEN",
  "telegram_chat_id": "YOUR_CHAT_ID",
  "email": "your@email.com",
  "check_interval_seconds": 60,
  "enabled_symbols": ["GOLD", "BTCUSD"],
  "min_setup_score": 7.0
}
```

## Managing Alerts

### List Active Alerts
```bash
python scripts/alert_monitor.py --list
```

### Remove Alert
```bash
python scripts/alert_monitor.py --remove GOLD_4500
```

### Pause All Alerts
```bash
python scripts/alert_monitor.py --pause
```

## Tips

- Set alerts for both sides (support AND resistance)
- Use setup alerts to catch opportunities while away
- Enable Telegram for mobile notifications
- Don't overuse - only for key levels
- Review triggered alerts to improve levels
