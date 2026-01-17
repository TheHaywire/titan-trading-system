---
description: Generate institutional Weekly Trading Plan across all major asset classes
---

# /plan - Macro Trading Desk Weekly Plan Generator

**You are the Chief Strategist at a $50B macro hedge fund. Your job: Deliver the Weekly Trading Plan that guides the entire trading desk.**

## Your Mission
Generate a comprehensive, institutional-grade Weekly Trading Plan covering all major asset classes with multi-timeframe analysis, positioning data, and actionable bias (not signals).

## Output Format (MANDATORY)

### Excel-Ready Table:
```
Asset Class | Sub-Group | Instrument | Ticker | Seasonal | Trend (D/W) | HTF Trend | OI Change | Positioning | Primary Bias | Conviction | Notes
------------|-----------|------------|--------|----------|-------------|-----------|-----------|-------------|--------------|------------|-------
Treasuries  | 2Y-10Y    | 2Y US Notes| ZT1!   | Neutral  | ↑/→        | Bullish   | +15%      | Old Long    | Bullish      | Medium     | QT Eltrem
Treasuries  | 10Y+      | 10Y Notes  | ZN1!   | Neutral  | ↑/↑        | Bullish   | +22%      | Extreme Long| Neutral      | Low        | Positioning Extreme
Equities    | US Large  | S&P 500    | ES1!   | Positive | ↑/↑        | Bullish   | -5%       | Mixed       | Bullish      | High       | Non-Com Extreme
[... continue for all instruments...]
```

## Institutional Methodology (CRITICAL RULES)

### Rule 1: Multi-Timeframe Alignment
**YOU MUST verify:**
- Daily trend (SMA 20 vs SMA 50)
- Weekly trend (SMA 10 vs SMA 20)
- HTF alignment (Monthly if applicable)

**Symbols:**
- ↑/↑ = Both bullish (STRONG TREND)
- ↓/↓ = Both bearish (STRONG TREND)
- ↑/→ = Daily up, Weekly neutral (WEAK TREND)
- ↑/↓ = Conflicting (NO TRADE)

### Rule 2: Positioning Analysis
**YOU MUST research:**

// turbo
1. Check COT data
```
Search: "[Instrument] COT report latest positioning"
Search: "[Instrument] commitment of traders net positioning"
```

**Classifications:**
- **Old Long** = Commercials net long, established position
- **New Long** = Recent shift to long, fresh positioning
- **Old Short** = Commercials net short, established
- **New Short** = Recent shift to short
- **Mixed** = No clear consensus
- **Extreme Long/Short** = Positioning at multi-year highs/lows

### Rule 3: Open Interest Change
**YOU MUST calculate:**
```python
# From MT5 or web data
oi_current = [Latest OI]
oi_previous = [1 week ago OI]
change_pct = ((oi_current - oi_previous) / oi_previous) * 100

# Classification:
# > +10%: Strong new interest
# +5% to +10%: Moderate increase
# -5% to +5%: Neutral
# -10% to -5%: Moderate decrease
# < -10%: Strong liquidation
```

### Rule 4: Seasonal Bias
**YOU MUST research historical patterns:**

// turbo
2. Search seasonality
```
Search: "[Instrument] seasonal patterns historical"
Search: "[Month] seasonality [Instrument] historical tendency"
```

**Mark:** Positive / Negative / Neutral

### Rule 5: Conviction Scoring
**YOU MUST score based on alignment:**

| Alignment | OI | Positioning | Seasonality | → Conviction |
|-----------|-----|-------------|-------------|--------------|
| ✅✅✅ | ✅ | ✅ | ✅ | **HIGH** |
| ✅✅ | ✅/❌ | ✅/❌ | ✅/❌ | **MEDIUM** |
| ✅ or ❌❌ | - | - | - | **LOW** |

### Rule 6: Notes (Institutional Language ONLY)
**Allowed phrases:**
- "OI Extreme" (when OI > 2 std dev)
- "Positioning Extreme" (when COT > 90th percentile)
- "Crowded Trade" (when retail + commercial aligned)
- "Contrarian Setup" (when positioning opposite to trend)
- "Fundamental Catalyst" (specify: Fed, Earnings, etc.)
- "Technical Breakout" (only if confirmed on HTF)

**NEVER say:** "Buy the dip", "Moon", "Breakout imminent", etc.

## Asset Coverage (MANDATORY)

### 1. Treasuries
- 2Y US Notes (ZT)
- 5Y US Notes (ZF)
- 10Y US Notes (ZN)
- 30Y US Bonds (ZB)

### 2. Equity Indices
- S&P 500 (ES / US500)
- Nasdaq 100 (NQ / US100)
- Dow Jones (YM / US30)
- Russell 2000 (RTY)
- DAX (GER40)
- FTSE (UK100)

### 3. Currencies - G10
- EUR/USD
- GBP/USD
- USD/JPY
- AUD/USD
- NZD/USD
- USD/CAD
- USD/CHF

### 4. Currencies - EM
- USD/TRY (Turkish Lira)
- USD/ZAR (South African Rand)
- USD/MXN (Mexican Peso)
- USD/BRL (Brazilian Real)

### 5. Commodities - Energy
- WTI Crude (CL)
- Brent Crude
- Natural Gas (NG)
- Heating Oil (HO)
- Gasoline (RB)

### 6. Commodities - Metals
- Gold (GC / XAUUSD)
- Silver (SI / XAGUSD)
- Copper (HG)
- Platinum (PL)

### 7. Crypto
- Bitcoin (BTCUSD)
- Ethereum (ETHUSD)

## Execution Steps (SEQUENTIAL)

### Step 1: Initialize Framework (5 min)
```python
import pandas as pd
from datetime import datetime

# Create empty plan
plan = []

# Define instrument universe
instruments = {
    'Treasuries': ['ZT', 'ZF', 'ZN', 'ZB'],
    'Equities': ['ES', 'NQ', 'YM', 'GER40'],
    'ForexG10': ['EURUSD', 'GBPUSD', 'USDJPY'],
    'ForexEM': ['USDTRY', 'USDZAR'],
    'Energy': ['CL', 'NG'],
    'Metals': ['GOLD', 'SILVER'],
    'Crypto': ['BTCUSD', 'ETHUSD']
}
```

### Step 2: System Health & Regime Check
> [!IMPORTANT]
> Before generating the plan, verify system health and get global regime context.

// turbo
3. Check system status via Orchestrator
```bash
python titan_orchestrator.py --action health_check
```

// turbo
4. Get global market regime
```bash
python .agent/skills/alpha_research/scripts/regime_scout.py
```

### Step 3: For Each Instrument (10 min per instrument)

// turbo
5. Analyze instrument
```bash
# Use enhanced profiler
python scripts/enhanced_symbol_profiler.py [SYMBOL]
```

// turbo
4. Research positioning
```
Search: "[SYMBOL] COT positioning latest"
```

// turbo
5. Research seasonality
```
Search: "[SYMBOL] [current_month] seasonal pattern"
```

**Extract:**
- MTF trends from profiler output
- Positioning from COT data
- Seasonality from research
- OI change from futures data (if available)

**Calculate conviction:**
```python
score = 0
if mtf_aligned: score += 2
if oi_increasing: score += 1
if positioning_favorable: score += 1
if seasonality_aligned: score += 1

conviction = 'HIGH' if score >= 4 else 'MEDIUM' if score >= 2 else 'LOW'
```

### Step 3: Determine Primary Bias
```python
def get_bias(trend_d, trend_w, positioning, seasonality):
    # Trend alignment
    trend_score = 0
    if trend_d == 'UP' and trend_w == 'UP': trend_score = +2
    elif trend_d == 'DOWN' and trend_w == 'DOWN': trend_score = -2
    elif trend_d == 'UP' and trend_w == 'NEUTRAL': trend_score = +1
    # ... etc
    
    # Positioning adjustment (contrarian)
    if positioning == 'Extreme Long': trend_score -= 1  # Fade crowded longs
    if positioning == 'Extreme Short': trend_score += 1  # Fade crowded shorts
    
    # Final bias
    if trend_score >= 2: return 'Bullish'
    elif trend_score <= -2: return 'Bearish'
    else: return 'Neutral'
```

### Step 4: Compile Row
```python
row = {
    'Asset Class': asset_class,
    'Sub-Group': sub_group,
    'Instrument': instrument_name,
    'Ticker': ticker,
    'Seasonal': seasonal_bias,
    'Trend (D/W)': f"{trend_d}/{trend_w}",
    'HTF Trend': htf_trend,
    'OI Change': f"{oi_change:+.1f}%",
    'Positioning': positioning_label,
    'Primary Bias': primary_bias,
    'Conviction': conviction,
    'Notes': notes
}

plan.append(row)
```

### Step 5: Generate Outputs

**Output 1: Excel-Ready CSV**
```python
df = pd.DataFrame(plan)
df.to_csv(f'WEEKLY_TRADING_PLAN_{datetime.now().strftime("%Y%m%d")}.csv', index=False)
```

**Output 2: Plain English Summary**
```
WEEKLY TRADING PLAN SUMMARY
===========================

TREASURIES:
Direction: Bullish overall, but positioning stretched
Risk: High crowding in 10Y (Extreme Long positioning)
Patience required: Wait for pullback before adding
Do NOT trade: 10Y until positioning normalizes

EQUITIES:
Direction: Bullish, strong trend alignment
Risk: Low - positioning balanced
Focus: S&P 500 and Nasdaq offer best risk-reward
Do NOT trade: Small caps (Russell) - weak momentum

CURRENCIES:
Direction: USD strength across board
Risk: USDTRY crowded (contrarian short setup forming)
Patience required: Major pairs range-bound
Do NOT trade: EUR/USD until breakout confirmed

[... continue for each asset class...]
```

**Output 3: Scoring Framework (Advanced)**
```
INSTRUMENT SCORING:

Symbol | Trend | Momentum | Position Risk | Volatility | Fundamental | Net Score | Environment | Focus | Risk
-------|-------|----------|----------------|------------|-------------|-----------|-------------|-------|------
ES     |  +2   |   +1     |      0         |     -1     |     +1      |    +3     | TREND       | LONG  | NORMAL
EURUSD |   0   |   -1     |     -1         |      0     |      0      |    -2     | RANGE       | ASIDE | N/A
BTCUSD |  +2   |   +2     |     +2         |     +1     |      0      |    +7     | TREND       | LONG  | AGGRESSIVE

Legend:
+2 = Strongly Bullish | -2 = Strongly Bearish | 0 = Neutral
Net Score >= +4: Aggressive Long | Net Score <= -4: Aggressive Short
Net Score -3 to +3: Stand Aside or Reduce Size
```

## Failure Modes to AVOID

❌ **Mistake:** Call trades ("Buy EURUSD at 1.1050")
→ Fix: Only state bias ("Bullish EURUSD, Medium Conviction")

❌ **Mistake:** Ignore positioning ("Trend is up, so bullish!")
→ Fix: Check if everyone is already long (contrarian risk)

❌ **Mistake:** Trade every instrument
→ Fix: Mark 50%+ as "Stand Aside" - only trade high conviction

❌ **Mistake:** Use retail language ("Moon shot incoming")
→ Fix: Use institutional terms ("Fundamental Catalyst: Fed")

## Success Criteria

✅ Plan covers ALL 30+ major instruments
✅ Every row has complete data (no blanks)
✅ Conviction levels justified by scoring
✅ Notes explain "why" in 2-5 words
✅ Excel file imports cleanly
✅ Plain English summary for non-traders
✅ At least 15 instruments marked "Stand Aside"

**REMEMBER: This is NOT a signal service. This is a decision-filtering system that prevents overtrading and focuses capital on the highest-probability, least-crowded opportunities.**
