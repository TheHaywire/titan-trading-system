---
description: Generate FULL professional-grade institutional trade setup with all 7 analysis layers
---

# Professional Institutional Trade Setup (7-Layer Analysis)

Generate a complete professional-grade trade setup covering all institutional analysis layers.

## Usage

```
/pro [SYMBOL]
```

**Examples:**
- `/pro SILVER` - Full 7-layer institutional setup for Silver
- `/pro GOLD` - Full institutional analysis for Gold
- `/pro EURUSD` - Complete setup for EUR/USD

## What It Generates

Complete 7-layer institutional analysis:

### 1️⃣ CURRENT MARKET STATE
- Current price, daily change %, volume
- Market structure (uptrend/downtrend/consolidation)
- Current trading session phase

### 2️⃣ MULTI-TIMEFRAME ANALYSIS (All 8 TFs)
- 1M, 5M, 15M, 30M, 1H, 4H, 1D, 1W
- RSI, ADX, Regime classification for each
- MTF alignment score (X/8)

### 3️⃣ TECHNICAL ANALYSIS LAYERS
**Price Action:**
- Support/Resistance zones with confluence
- Fibonacci retracement levels
- Chart patterns (triangles, engulfing, etc.)

**Smart Money Signals:**
- Order flow analysis
- Institutional buy/sell zones
- Volume confirmation

**Momentum Indicators:**
- MACD, Stochastic, CCI, Williams %R
- RSI divergences
- ADX trend strength

### 4️⃣ TRADE SETUP GENERATION
- 3 Entry options (Aggressive/Conservative/Safer)
- 3 Stop Loss levels (Tight/Normal/Wide)
- 4 Take Profit targets (TP1-TP4)
- Risk/Reward calculations for each

### 5️⃣ PROBABILITY ANALYSIS
- Main scenario probability
- 4-hour probability matrix
- Alternative scenarios

### 6️⃣ ORDER FLOW INTERPRETATION
- Institutional buy/sell zones
- Order flow imbalance visualization
- Confidence level (High/Medium/Low)

### 7️⃣ PROFESSIONAL ASSESSMENT
- Overall setup quality rating (1-10)
- Time to potential breakout
- Position sizing recommendations
- Risk management checklist

## How to Run

// turbo-all
0. **First, check system health via Orchestrator:**
```powershell
python titan_orchestrator.py --action health_check
```
> [!IMPORTANT]
> If system status is DEGRADED or any department shows BLOCK, consider waiting for conditions to clear before generating a setup.

1. Run TA-Lib Enhanced Profiler
```powershell
python scripts/symbol_profiler_v3.py SILVER
```

2. Run Institutional Market Analyst  
```powershell
python scripts/institutional_market_analyst.py SILVER
```

3. Generate Ultimate Setup  
```powershell
python scripts/ultimate_setup_generator.py SILVER
```

4. **Run Pre-Trade Hook before acting on the setup:**
```powershell
python .agent/hooks/pre_trade.py --symbol SILVER --direction [BUY/SELL] --lots [SIZE]
```

5. View the generated reports in `analysis/` and `intelligence/` folders

## Output Files

| File | Contents |
|------|----------|
| `analysis/SYMBOL_YYYYMMDD_HHMMSS.md` | MTF Analysis |
| `intelligence/SYMBOL_TALIB_v3_YYYYMMDD_HHMMSS.md` | 158 Indicators |
| `analysis/SYMBOL_MASTER_SETUP_YYYYMMDD_HHMMSS.md` | Trade Setup |
| `charts/SYMBOL_*_YYYYMMDD_HHMMSS.png` | Visual Charts |

## Quality Standards

The generated setup includes:
- ✅ 100+ technical indicators via TA-Lib
- ✅ 61 candlestick pattern scans
- ✅ Multi-timeframe confluence zones
- ✅ Fibonacci retracement levels
- ✅ Risk/Reward calculations with 1:2+ ratio
- ✅ Probability matrices
- ✅ Professional quality rating (1-10)
- ✅ Actionable entry/SL/TP levels

## Tips

- Use for swing trades and position trades
- Wait for pullbacks when RSI is overbought
- Target 1:2+ R:R for conservative entries
- Check confluence zones for highest probability
- Review probability matrix before entry
