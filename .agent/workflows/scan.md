---
description: Scan multiple symbols and find the best trading opportunities
---

# Multi-Symbol Opportunity Scanner

Automatically analyze your entire watchlist and identify the highest-quality trading setups across all markets.

## Usage

```
/scan
```

This will analyze all symbols in your watchlist and rank them by opportunity quality.

## What It Does

Scans multiple symbols simultaneously:

✅ **Analyzes All Symbols** in your watchlist (GOLD, BTCUSD, EURUSD, etc.)
✅ **Quality Scores** each setup (0-10 rating)
✅ **Ranks Opportunities** from best to worst
✅ **Identifies Ready Setups** with favorable R:R
✅ **Multi-Timeframe** confirmation for each
✅ **Action Plans** for top 3 setups
✅ **Saves Summary Report** with all findings

## How to Run

// turbo
1. Run the opportunity scanner via the **Unified Orchestrator**
```bash
python titan_orchestrator.py --action scan
```

Or use the legacy scanner for more detailed output:
```bash
python scripts/opportunity_scanner.py
```

The scanner will:
- **Check system health** via Infrastructure skills first
- **Filter by macro environment** (blocks during high-impact news)
- Analyze 10+ symbols using Data Intelligence + Alpha Research skills
- Score each setup based on confluence, R:R, trends
- Generate a ranked list of opportunities
- Save detailed report to `analysis/OPPORTUNITIES_YYYYMMDD.md`

## Output

**Ranked Opportunity List**:
```
🥇 GOLD - 8.5/10 - Bullish Pullback Setup
   Entry: 4407.50 | SL: 4380 | TP: 4500 | R:R 3.4:1

🥈 BTCUSD - 7.2/10 - Breakout Setup
   Entry: 94500 | SL: 93000 | TP: 97000 | R:R 1.7:1

🥉 EURUSD - 6.8/10 - Range Trade
   Entry: 1.0950 | SL: 1.0920 | TP: 1.1000 | R:R 1.7:1
```

## Configuration

Edit `config/watchlist.json` to customize symbols:
```json
{
  "symbols": ["GOLD", "BTCUSD", "EURUSD", "GBPUSD", "US100"],
  "min_quality_score": 6.0,
  "max_results": 5
}
```

## Tips

- Run daily before trading session
- Focus on 7+/10 setups only
- Compare opportunities across markets
- Use when unsure which symbol to trade
