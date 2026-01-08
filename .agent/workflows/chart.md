---
description: Generate professional visual charts with analysis overlays
---

# Visual Chart Generator

Create professional-quality charts with all analysis elements visualized (support/resistance, patterns, Fibonacci, entry zones).

## Usage

```
/chart [SYMBOL] [TIMEFRAME]
```

**Examples:**
- `/chart GOLD 4H` - Generate 4H chart for Gold
- `/chart BTCUSD 1D` - Generate daily chart for Bitcoin
- `/chart EURUSD 1H` - Generate hourly chart for EUR/USD

## What It Does

Generates beautiful charts with:

✅ **Candlestick Price Action** with proper styling
✅ **Support & Resistance Lines** color-coded
✅ **Fibonacci Retracements** with level labels
✅ **Moving Averages** (9, 21, 55, 200)
✅ **Entry/Exit Zones** highlighted
✅ **Patterns Marked** (triangles, flags, divergences)
✅ **RSI Indicator** subplot
✅ **Volume Bars** at bottom
✅ **Annotations** for key levels

## How to Run

// turbo
1. Generate chart for a symbol
```bash
python scripts/visual_chart_generator.py GOLD 4H
```

Output saved to: `charts/GOLD_4H_YYYYMMDD.png`

## Chart Features

**Main Panel:**
- Candlesticks (green/red)
- Support lines (blue, dashed)
- Resistance lines (red, dashed)
- Fibonacci levels (orange, dotted)
- Entry zone (green shaded area)
- Patterns highlighted

**Indicator Panel:**
- RSI with overbought/oversold zones
- Volume bars

**Annotations:**
- Key price levels labeled
- Pattern names shown
- Trade setup boxes

## Configuration

Customize chart appearance in `config/chart_settings.json`:
```json
{
  "style": "dark",  // or "light"
  "width": 1920,
  "height": 1080,
  "show_ma": true,
  "show_fib": true,
  "show_patterns": true
}
```

## Tips

- Use 4H charts for swing trading
- Use 1H for day trading entries
- Save charts for your trading journal
- Share charts in trading groups
- Print for physical analysis
