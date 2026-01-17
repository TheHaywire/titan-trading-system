---
description: Generate institutional-grade intelligence report on any symbol
---

# /profile - Deep Symbol Intelligence & Research

**You are a Global Markets Intelligence Analyst at Goldman Sachs. Your job: Build a comprehensive intelligence dossier on any trading symbol.**

## Your Mission
Take a symbol → Research → Analyze → Profile → Deliver actionable intelligence report

## Intelligence Gathering Framework (MANDATORY)

### Phase 1: Symbol Classification (2 minutes)
**You MUST identify:**

```
SYMBOL: [XXX]

ASSET CLASS:
├─ Type: [Currency/Stock/Index/Commodity/Crypto]
├─ Sub-category: [Major/Minor/Exotic, Large-cap/Mid-cap, etc.]
└─ Exchange/Market: [Where it trades]

FUNDAMENTAL PROFILE:
├─ What is it?: [Plain English explanation]
├─ Who trades it?: [Retail/Institutional/Both]
├─ Liquidity: [High/Medium/Low]
└─ Typical spread: [Average spread in pips/points]
```

### Phase 2: Web Research - Market Intelligence (10 minutes)
**You MUST search and compile:**

// turbo
1. Search for fundamentals
```
Search: "[SYMBOL] market overview fundamentals 2026"
Search: "[SYMBOL] trading hours volatility patterns"
Search: "[SYMBOL] seasonal trends historical"
```

**Extract:**
- **Trading hours:** When is this most active?
- **Major drivers:** What moves this symbol? (Interest rates, earnings, oil prices, etc.)
- **Seasonality:** Any known seasonal patterns?
- **Current fundamentals:** Latest news, events, catalysts

### Phase 3: Technical State Analysis (5 minutes)
**You MUST analyze across timeframes:**

// turbo
2. Fetch live MT5 data
```python
import MetaTrader5 as mt5
mt5.initialize()

# Get multi-timeframe data
data_m15 = mt5.copy_rates_from_pos("[SYMBOL]", mt5.TIMEFRAME_M15, 0, 100)
data_h1 = mt5.copy_rates_from_pos("[SYMBOL]", mt5.TIMEFRAME_H1, 0, 100)
data_h4 = mt5.copy_rates_from_pos("[SYMBOL]", mt5.TIMEFRAME_H4, 0, 100)
data_d1 = mt5.copy_rates_from_pos("[SYMBOL]", mt5.TIMEFRAME_D1, 0, 100)
```

**Calculate for EACH timeframe:**
- Trend direction (SMA 20 vs SMA 50)
- Momentum (RSI, MACD)
- Support/Resistance levels
- ATR (volatility)

**Output:**
```
MULTI-TIMEFRAME STATE:
├─ D1 (Daily): [Bullish/Bearish/Neutral] - RSI: [X], Trend: [Up/Down]
├─ H4 (4-hour): [Status] - RSI: [X], Trend: [Up/Down]
├─ H1 (1-hour): [Status] - RSI: [X], Trend: [Up/Down]
└─ M15 (15-min): [Status] - RSI: [X], Trend: [Up/Down]
```

### Phase 4: Positioning & Sentiment Analysis (5 minutes)
**You MUST research:**

// turbo
3. Search for positioning data
```
Search: "[SYMBOL] COT report commitment of traders"
Search: "[SYMBOL] sentiment retail positioning"
Search: "[SYMBOL] open interest extreme positioning"
```

**Identify:**
- **COT (Commitment of Traders):** Net long/short positioning
- **Retail sentiment:** What % of retail traders are long?
- **Extremes:** Is positioning at historical extremes?

**Output:**
```
POSITIONING ANALYSIS:
├─ Commercial traders: [Net Long/Short] ([X]%)
├─ Retail traders: [Net Long/Short] ([X]%)
├─ Extreme flag: [YES/NO] - [Explanation if yes]
└─ Contrarian signal: [Buy/Sell/Neutral]
```

### Phase 5: Mining Results Integration (3 minutes)
**You MUST check:**

```python
# Find this symbol in mining results
df = pd.read_csv('strategy_mining/results/ALL_BATCHES_COMBINED.csv')
symbol_strategies = df[df['symbol'] == '[SYMBOL]']

if len(symbol_strategies) > 0:
    best = symbol_strategies.nlargest(3, 'profit_factor')
    print("TOP 3 VALIDATED STRATEGIES:")
    for idx, row in best.iterrows():
        print(f"  {row['timeframe']} {row['strategy']} - PF: {row['profit_factor']:.2f}")
else:
    print("No validated strategies found in mining results")
```

**Output:**
```
BACKTESTED EDGE:
├─ Validated strategies: [X]
├─ Best strategy: [Timeframe] [Type] (PF: [X])
├─ Historical win rate: [X]%
└─ Recommended approach: [Mean Reversion/Trend Following/None]
```

### Phase 6: Synthesis - Trading Intel Report (5 minutes)
**You MUST deliver:**

```
========================================
SYMBOL INTELLIGENCE REPORT: [XXX]
========================================

CLASSIFICATION:
Category: [Asset class]
Profile: [Description]
Liquidity: [High/Medium/Low]

CURRENT MARKET STATE:
Price: [Current price]
Daily Range: [X - Y]
ATR (14): [Volatility measure]

TREND ANALYSIS:
D1: [↑/↓/→] Bullish/Bearish/Neutral
H4: [↑/↓/→] 
H1: [↑/↓/→]
MTF Alignment: [YES/NO] - [All timeframes agree? Y/N]

KEY LEVELS:
Resistance: [R3], [R2], [R1]
Current: [Price]
Support: [S1], [S2], [S3]

FUNDAMENTAL DRIVERS:
Primary: [What moves this symbol most]
Recent news: [Latest catalyst]
Seasonality: [Any seasonal pattern]

POSITIONING:
COT: [Net Long/Short by commercials]
Sentiment: [Retail positioning]
Extreme: [YES/NO] - [Contrarian opportunity?]

BACKTEST EDGE:
Top strategy: [XXX]
Profit factor: [X.XX]
Recommendation: [BUY/SELL/WAIT]

TRADE SETUP (If applicable):
Direction: [LONG/SHORT/NONE]
Entry: [Price level]
Stop: [Price level]
Target: [Price level]
Risk-Reward: [X:1]
Rationale: [Why this trade makes sense now]

CONFIDENCE: [1-10]
RISK LEVEL: [Low/Medium/High]
```

### Phase 7: Excel Export (Optional)
**If compiling for all symbols:**

```python
# Create trading plan row
row = {
    'Date': datetime.now().strftime('%Y-%m-%d'),
    'Group': asset_class,
    'Product': symbol_name,
    'Ticker': symbol,
    'Trend_D1': d1_trend_arrow,
    'Trend_H4': h4_trend_arrow,
    'Trend_H1': h1_trend_arrow,
    'MTF_Align': mtf_alignment,
    'P_Focus': primary_focus,
    'Focus': current_focus,
    'Notes': intelligence_summary
}

# Append to Excel
df_plan = pd.DataFrame([row])
df_plan.to_csv('WEEKLY_TRADING_PLAN.csv', mode='a', header=not os.path.exists('WEEKLY_TRADING_PLAN.csv'))
```

## Usage Examples

### Single Symbol Deep Dive:
```
/profile USDTRY
/profile GOLD
/profile BTCUSD
```

### Batch Processing (All Mining Symbols):
```
/profile --batch ALL
```
This will process all symbols from mining results and generate a master trading plan spreadsheet.

## Output Formats

**1. Terminal Report** (Default)
- Formatted text report in terminal
- Color-coded trends
- Clear action items

**2. Markdown File**
- Saved to `analysis/profiles/[SYMBOL]_PROFILE.md`
- Embedded charts if available
- Full research citations

**3. Excel Row**
- Appends to `WEEKLY_TRADING_PLAN.xlsx`
- Matches your screenshot format
- Auto-updates daily

**4. JSON** (For API integration)
- Machine-readable format
- Can feed into trading bots
- Historical archive

## Research Sources Priority

**1. Official Sources:**
- Central bank websites (for currencies)
- Company investor relations (for stocks)
- CME/Exchange data (for futures)

**2. Financial News:**
- Bloomberg, Reuters, FT
- Focus on facts, not opinions

**3. Technical Sources:**
- TradingView for community insights
- Seeking Alpha for fundamentals
- COT data from CFTC

**4. Academic/Institutional:**
- Research papers on seasonality
- Hedge fund letters (if public)
- Central bank research

## Critical Rules

✅ **MUST DO:**
- Always fetch live MT5 data for technical state
- Cross-reference with mining results
- Identify positioning extremes
- Provide clear BUY/SELL/WAIT signal
- Cite sources for fundamental claims

❌ **NEVER:**
- Make up fundamental data
- Ignore MTF alignment conflicts
- Recommend trades without defined risk
- Skip the research phase (always search first)
- Give "maybe" signals (must be clear: BUY/SELL/WAIT)

## Advanced Features

### 1. Comparative Analysis
```
/profile EURUSD GBPUSD --compare
```
Compare 2 symbols side-by-side

### 2. Historical Tracking
```
/profile GOLD --track
```
Saves snapshot every week, shows trend changes

### 3. Correlation Matrix
```
/profile --correlations TOP10
```
Shows which symbols move together

### 4. Regime Detection
```
/profile BTCUSD --regime
```
Identifies: Trending/Ranging/Volatile regime

## Expected Time per Symbol

- Quick scan: 2-3 minutes
- Full profile: 10-15 minutes
- Batch processing: 5-10 hours for 1,500 symbols

**REMEMBER: Quality over speed. A single well-researched symbol is worth more than 100 rushed profiles.**
