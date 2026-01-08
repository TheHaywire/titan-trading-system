---
description: Generate comprehensive institutional-grade market analysis with visual charts
---

# Institutional Market Analysis with Visual Charts

Generate a complete multi-timeframe market analysis report with embedded visual charts.

## Usage

```
/analyze [SYMBOL]
```

**Examples:**
- `/analyze GOLD` - Analyze Gold with visual charts
- `/analyze BTCUSD` - Analyze Bitcoin with charts
- `/analyze EURUSD` - Analyze EUR/USD with charts

## What It Generates

Complete analysis package including:

✅ **Multi-Timeframe Analysis** (1M, 5M, 15M, 30M, 1H, 4H, 1D, 1W)
✅ **Visual Charts** - Embedded charts for key timeframes (1W, 1D, 4H, 1H)
✅ **Technical Indicators** - RSI, Moving Averages, ATR, ADX, Bollinger Bands
✅ **Pattern Detection** - Candlestick & chart patterns
✅ **Support & Resistance** - Auto-detected levels
✅ **Fibonacci Levels** - Auto-calculated retracements
✅ **Confluence Zones** - Multi-timeframe overlap areas
✅ **Action Plans** - IF-THEN trading scenarios
✅ **Trader Recommendations** - Position/Swing/Day strategies
✅ **Ready Setups** -Entry/SL/TP with R:R ratios

## How to Run

// turbo
1. Set encoding and run the complete analyst
```powershell
$env:PYTHONIOENCODING='utf-8'; python scripts/institutional_market_analyst.py GOLD
```

2. Generate visual charts for key timeframes
```powershell
python scripts/visual_chart_generator.py GOLD 1W
python scripts/visual_chart_generator.py GOLD 1D
python scripts/visual_chart_generator.py GOLD 4H
python scripts/visual_chart_generator.py GOLD 1H
```

3. Enhance the report with action plans
```powershell
python scripts/enhance_report.py analysis\GOLD_YYYYMMDD_HHMMSS.md
```

## Output

- **Location**: `analysis/SYMBOL_YYYYMMDD_HHMMSS.md`
- **Charts**: `charts/SYMBOL_TIMEFRAME_YYYYMMDD_HHMMSS.png`
- **Format**: Professional markdown with embedded charts

## Features

### Visual Charts Include:
- Candlestick price action
- Moving averages (9, 21, 55)
- Support & resistance lines (blue/red dashed)
- Current price indicator (green solid)
- Fibonacci levels (orange dotted)
- RSI subplot with 30/70 zones

### Report Sections:
1. Executive Summary - Multi-TF trend table
2. Detailed Timeframe Analysis - Each TF with chart
3. Confluence Zones - High probability areas
4. Action Plan - IF-THEN scenarios
5. Trader Recommendations - Position/Swing/Day
6. Ready Setups - Complete trade plans

## Tips

- Charts make it easy to visualize support/resistance
- Compare visual charts with textual analysis
- Use 1D/4H charts for swing trading
- Use 1H chart for intraday entries
- Save charts for trading journal
