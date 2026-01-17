# FINVIZ SCREENER CATALOG: THE COMPLETE EDUCATIONAL GUIDE

This is your ultimate guide to understanding and using every Finviz screener. Each section explains the concept, when to use it, and how to profit from it.

---

## 📚 CORE CONCEPTS EXPLAINED

### What is a Stock Screener?
A screener filters 8000+ stocks down to a handful that meet specific criteria. Think of it like a search engine for trading opportunities.

**Why Screeners Matter:**
- **Save Time**: Instead of manually checking hundreds of charts, the screener does it in seconds
- **Remove Emotion**: Systematic rules prevent impulse trading
- **Find Hidden Gems**: Discover stocks you'd never notice manually

### The 3 Pillars of Screening
1. **Fundamental** (Company Health) - Is the business profitable?
2. **Technical** (Price Action) - Is the stock in a trend?
3. **Sentiment** (Market Psychology) - Are institutions buying or selling?

## PRESET SCREENERS (Pre-Built)

Finviz provides ready-made screeners organized by strategy:


## I. MOMENTUM SCREENERS (Ride the Wave)

These screeners find stocks that are moving fast. Momentum trading is about catching existing trends, not predicting reversals.

### 1. **Top Gainers** 🚀
**Concept:** Stocks with the biggest % price increase today.

**How It Works:**
- Scans all stocks for today's price change
- Ranks by % gain (highest first)
- Typical results: +5% to +50% daily moves

**When to Use:**
- **Morning Scan (9:35 AM)**: Find early momentum stocks
- **Mid-Day Scan (12:00 PM)**: Identify sustained strength
- **Never use pre-market**: Volume is too low, prices are fake

**Trading Strategy:**
```
IF stock is Top Gainer (+10%)
AND Relative Volume > 2.0 (institutional participation)
AND Price > $5 (avoid penny stocks)
THEN: Look for pullback entry (don't chase the top)
```

**Real Example:**
- Stock: NVDA gains +12% on earnings beat
- Finviz shows it as #1 Top Gainer at 10 AM
- **Good Trade**: Wait for pullback to VWAP, enter on bounce
- **Bad Trade**: Buy at +12% peak, get stopped out on reversal

**Risk:** Buying at the top. Always wait for consolidation.

---

### 2. **Most Volatile** ⚡
**Concept:** Stocks with the widest intraday price swings.

**How It Works:**
- Measures distance between daily high and low
- Filters stocks by Average True Range (ATR)
- High volatility = More profit potential (and risk)

**When to Use:**
- **Scalping**: Need big moves in short timeframes
- **Options Trading**: Volatility = Premium
- **Avoid if**: You're a conservative investor

**Trading Strategy:**
```
IF Daily Range > 5%
AND Volume increasing
THEN: Trade breakouts with tight stops
```

**Real Example:**
- Stock swings between $48-$52 in one day (8% range)
- You scalp $50 → $51 breakout in 15 minutes
- Volatility creates multiple entry opportunities

**Key Metric:** ATR (Average True Range)
- ATR = 3.0 means stock typically moves $3/day
- Use ATR to set stop losses: `SL = Entry - (2 × ATR)`

---

### 3. **New High** (Breakout Hunter) 📈
**Concept:** Stocks breaking 52-week price highs.

**Why This Matters:**
- No overhead resistance (all sellers are profitable)
- Institutional momentum (big money breaking new ground)
- Often continues for days/weeks

**When to Use:**
- Bull markets (2024-2025 tech rally)
- Avoid during crashes (2020 COVID, 2022 Fed hikes)

**Trading Strategy:**
```
IF Price breaks 52W High
AND Volume > 2× average (conviction)
AND Not extended (< 10% above breakout)
THEN: Enter with stop below breakout level
```

**Pattern Recognition:**
- **Cup and Handle**: Stock consolidates for 3+ months, then breaks out
- **Flat Top Breakout**: Stock tests same resistance 3-4 times, finally breaks

**Caution:** Beware "false breakouts"
- Check if it's just a 0.1% new high (noise) or a meaningful 5%+ breakout

---

### 4. **Unusual Volume** 📊
**Concept:** Volume 5x-10x higher than normal.

**Why Volume Matters:**
- **High Volume = Institutional Activity** (smart money)
- **Low Volume = Retail Noise** (random fluctuations)

**The "Something's Happening" Signal:**
When a stock that normally trades 100K shares/day suddenly trades 2M shares, there's a REASON:
- Earnings surprise
- Merger/Acquisition rumor
- Insider buying leak
- Analyst upgrade

**How to Use:**
1. **Morning**: Scan for unusual volume at market open
2. **Check News**: Why is volume surging?
3. **Validate Direction**: Is price moving with volume or against it?

**Trading Strategy:**
```
IF Relative Volume > 5×
AND Price moving up
AND News = Positive OR Unknown
THEN: Enter with momentum, exit if volume dies
```

**Red Flag:** High volume + price dropping = Distribution (institutions selling)

---

### 5. **Overbought (RSI > 70)** 🔴
**Concept:** Stock has risen too far, too fast. Reversal likely.

**What is RSI?**
- **Relative Strength Index** (14-day default)
- Scale: 0-100
- **> 70 = Overbought** (overheated, likely to pullback)
- **< 30 = Oversold** (beaten down, likely to bounce)

**The Paradox:**
- Overbought stocks often keep going higher (momentum)
- But they're vulnerable to sudden reversals

**When to Use:**
- **Contrarian: Short/Sell** when RSI > 80 AND price hits resistance
- **Momentum: Buy** when RSI > 70 if the trend is strong (let winners run)

**Trading Strategy (Reversal Play):**
```
IF RSI > 75
AND Stock near resistance
AND Volume declining (exhaustion)
THEN: Short OR wait for lower entry
```

**Example:**
- Tesla hits RSI 85 after 5 green days
- Hits $300 resistance (previous rejection level)
- **Smart Play**: Wait for pullback to RSI 50, then re-enter long

---

### 6. **Oversold (RSI < 30)** 🟢
**Concept:** Stock has fallen too far, bounce likely.

**The "Dead Cat Bounce" Risk:**
- Oversold doesn't mean "must bounce"
- Stocks can stay oversold for weeks during bear markets

**When RSI < 30 Works:**
- **In uptrends**: Temporary dip, buy the discount
- **Strong companies**: Good business, bad temporary news

**When RSI < 30 Fails:**
- **In downtrends**: "Falling knives" keep falling
- **Weak companies**: Fundamental issues, avoid

**Trading Strategy (Value Bounce):**
```
IF RSI < 25
AND 200-Day MA trending up (long-term uptrend)
AND No bad fundamental news
THEN: Enter with tight stop, target RSI 50
```

**Pro Tip:** Combine with Support Levels
- RSI < 30 + Bouncing off major support = High probability trade

---

### 7. **Recent Insider Buying** 💼
**Concept:** Company executives are buying their own stock.

**Why This Is Powerful:**
- **Insiders know more than you**: They see the quarterly numbers before anyone
- **Legal insider trading**: They file SEC Form 4 within 2 days of trade
- **High conviction signal**: CEOs don't buy unless they're confident

**Types of Insiders:**
1. **CEO/CFO** - Most powerful signal
2. **Board of Directors** - Strong signal
3. **10% Owners (Hedge Funds)** - Very strong (big money)

**Red Flags (Ignore These):**
- **Stock Options Exercise**: Not a "buy", just cashing in compensation
- **Single Share Buys**: Symbolic gesture, not meaningful
- **Scheduled Buying Plans**: Pre-programmed, not opportunistic

**Trading Strategy:**
```
IF Multiple insiders buying (3+)
AND Total value > $1M
AND Stock near 52W Low
THEN: Enter long, target 20% gain
```

**Real Example:**
- Meta (Facebook) insiders buy $50M worth at $90/share in Nov 2022
- Stock rallies to $180 within 6 months
- Insiders knew AI pivot was coming

---

### 8. **Unusual Volume + Insider Buying (Combo Screener)**
**The "Something Big Brewing" Signal**

This is the ULTIMATE early-stage setup:
```
Insider Buying (last 7 days) 
+ Unusual Volume (today)
+ No public news yet
= Major catalyst coming
```

**What's Happening:**
- Insiders bought last week (they know something)
- Volume surges today (word is leaking)
- News hasn't broken yet (you're early)

**How to Trade:**
1. Enter immediately (before news breaks)
2. Set stop below recent low
3. Hold through news announcement
4. Exit when RSI > 70 (hype peak)

---

### 9. **Earnings Calendar (Earnings Before/After)** 📅
**Concept:** Stocks reporting quarterly earnings soon.

**Why Earnings Matter:**
- **Volatility Spike**: 10-20% moves in either direction
- **Trend Reversal**: Bad companies miss, good companies beat
- **Options Premium**: IV (Implied Volatility) skyrockets

**3 Strategies:**

**Strategy A: Earnings Momentum Play**
```
IF Stock trending up before earnings
AND Analyst estimates conservative
THEN: Buy 1-2 days before, sell after earnings
```

**Strategy B: Contrarian**
```
IF Stock beaten down for 3 months
AND Estimates are low (pessimistic)
THEN: Buy before earnings, expecting surprise beat
```

**Strategy C: Volatility Fade**
```
Wait until AFTER earnings
Enter on the pullback (profit-taking)
Ride the trend that emerges
```

**Risk Management:**
- **Never hold full size through earnings** (unless you love gambling)
- Reduce position by 50% before report
- Use options spreads to define risk

---

## II. BEARISH/CONTRARIAN SCREENERS (Profit from Pain)


These screeners find stocks that are falling or facing trouble. Contrarian trading = buying fear, selling greed.

### 10. **Top Losers** 📉
**Concept:** Stocks with the biggest % price decline today.

**Two Ways to Trade:**
1. **Fade the Panic** (Contrarian): Buy oversold bounces
2. **Ride the Crash** (Momentum): Short weak stocks

**Contrarian Strategy:**
```
IF Top Loser (-15%)
AND Strong fundamentals (P/E < 20, Revenue growing)
AND Hits major support level
THEN: Buy the panic, target mean reversion
```

**Momentum Short Strategy:**
```
IF Top Loser (-20%)
AND Weak fundamentals (Debt high, Revenue declining)
AND Breaks support
THEN: Short with tight stop, ride the trend
```

**Warning:** "Catching falling knives" can cut you. Always wait for stabilization (consolidation).

---

### 11. **Most Shorted** ⚠️
**Concept:** Stocks with highest % of float sold short.

**What Does This Mean?**
- **Short Interest**: Traders betting the stock will fall
- **Short Squeeze**: If price rises, shorts must buy to cover (fuel for explosive rallies)

**High Short Interest Signals:**
- **Bearish**: Institutions expect trouble (bankruptcy, earnings miss)
- **Bullish (Squeeze)**: If positive news hits, shorts trapped = massive rally

**The Famous Squeezes:**
- GameStop (2021): 140% short interest → +2000% squeeze
- Tesla (2020): 20% short interest → Shorts lose $40B
- Volkswagen (2008): Biggest squeeze in history

**Trading Strategy (Squeeze Play):**
```
IF Short Float > 30%
AND Price breaks above resistance
AND Volume surging
THEN: Buy for squeeze, exit when shorts capitulate (volume spike)
```

**Risk:** High short interest exists for a REASON. Many shorted stocks go to zero.

---

### 12. **Recent Insider Selling** 🚨
**Concept:** Executives are selling their stock.

**The Dark Signal:**
While insider buying = bullish, insider selling = ???

**When Insider Selling is NORMAL:**
- CEOs selling 5-10% of holdings (diversification)
- Pre-scheduled selling plans (10b5-1)
- Selling to pay taxes on stock options

**When Insider Selling is ALARMING:**
- **Multiple insiders selling simultaneously** (coordinated exit)
- **Selling 50%+ of their holdings** (panic)
- **Selling right before earnings** (they know it's bad news)

**Red Flag Example:**
- Enron executives sold $1.1B worth before collapse (2001)
- Lehman Brothers CEOs sold months before bankruptcy (2008)

**Trading Strategy (Avoidance):**
```
IF CEO sells > 25% of holdings
AND Multiple C-Suite executives selling
THEN: Exit or avoid, regardless of price action
```

---

## III. VALUE SCREENERS (Buy Quality Cheap)

Value investing = Buying $1 for 50 cents. Focus on fundamentals, not momentum.

### 13. **Undervalued Large Caps** 💎
**Concept:** Big companies trading below intrinsic value.

**Key Metrics:**
- **P/E < 15** (Price to Earnings)
- **P/B < 2** (Price to Book Value)
- **Dividend Yield > 3%**
- **Market Cap > $10B** (established companies)

**Why This Works:**
- Large caps can't grow fast, so market undervalues them
- Eventually, value gets recognized (catalyst: earnings beat, dividend increase)
- Low risk: These companies aren't going bankrupt

**Buffett's Formula:**
```
IF P/E < Industry Average
AND ROE > 15% (Return on Equity)
AND Debt/Equity < 0.5 (conservative balance sheet)
AND Dividend increasing for 10+ years
THEN: Buy and hold for years
```

**Real Example:**
- Apple 2016: P/E of 10 (market worried about iPhone sales)
- Fundamentals strong: $200B cash, loyal customers
- Stock doubles in 2 years as market realizes value

---

### 14. **High Dividend Yield** 💰
**Concept:** Stocks paying 5%+ annual dividends.

**The Income Play:**
- Instead of trading for capital gains, collect cash payments
- Dividends provide downside protection (floor on price)

**Warning Signs (Dividend Traps):**
- **Dividend Yield > 10%**: Unsustainable, likely to be cut
- **Payout Ratio >** 100%: Company paying more than it earns

**Safe Dividend Checklist:**
```
IF Dividend Yield 4-7%
AND Payout Ratio < 70%
AND Dividend growing for 5+ years
AND Debt/Equity < 1.0
THEN: Safe income investment
```

**Dividend Aristocrats:**
Companies that increased dividends for 25+ consecutive years:
- Johnson \u0026 Johnson (JNJ)
- Coca-Cola (KO)
- Procter \u0026 Gamble (PG)

---

### 15. **PEG Ratio < 1** (Growth at Reasonable Price)
**Concept:** The "smart growth" metric.

**What is PEG?**
- PEG = P/E Ratio ÷ EPS Growth Rate
- **PEG < 1** = Undervalued growth
- **PEG > 2** = Overvalued growth

**Example:**
- Stock A: P/E = 30, EPS Growth = 10% → PEG = 3.0 (expensive)
- Stock B: P/E = 30, EPS Growth = 40% → PEG = 0.75 (cheap!)

**Peter Lynch's Rule:**
"Never pay more than the growth rate for a stock."
- If growth = 25%, max P/E should be 25
- If P/E = 20 and growth = 25%, you got a bargain

**Trading Strategy:**
```
IF PEG < 1.0
AND Revenue growing > 15%/year
AND Profit Margin > 10%
THEN: Buy and hold until PEG > 2.0
```

---

## IV. TECHNICAL PATTERN SCREENERS (Chart Reading)

These screeners auto-detect chart patterns you'd normally find manually.

### Chart Patterns Explained

**1. Head \u0026 Shoulders (Reversal)**
```
      /\      ← Head (Highest Peak)
     /  \
  /\/    \/\   ← Shoulders
────────────── ← Neckline
```
- **Bearish Pattern**: Price tops out, reversal coming
- **Trade**: Short when neckline breaks

**2. Double Bottom (Reversal)**
```
\  /\  /    ← Two equal lows
 \/  \/
```
- **Bullish Pattern**: Support tested twice, buyers defend
- **Trade**: Buy when price breaks above middle peak

**3. Ascending Triangle (Continuation)**
```
  ________  ← Flat resistance
 /    /      ← Higher lows
/____/
```
- **Bullish Pattern**: Buyers getting aggressive
- **Trade**: Buy breakout above resistance

**4. Wedge Up/Down**
- **Rising Wedge**: Bearish (momentum dying)
- **Falling Wedge**: Bullish (sellers exhausted)

**5. Channel**
- Price moves between parallel lines
- Trade bounces off channel edges

---

## V. HOW TO BUILD CUSTOM SCREENERS

Combine multiple filters for ultra-specific setups:

**Example 1: "Undervalued Squeeze Play"**
```
Market Cap > $1B
Short Float > 20%
P/E < 15
RSI < 35
= Oversold value stock with squeeze potential
```

**Example 2: "Institutional Momentum"**
```
Relative Volume > 3
Insider Buying (Last Week)
52W High
Price > $20
= Big money accumulating breakout
```

**Example 3: "Dividend Growth Value"**
```
Dividend Yield 3-6%
Dividend growth > 5%/year
P/E < 18
Debt/Equity < 0.8
= Safe income with growth potential
```

---

## VI. AUTOMATION IN YOUR SYSTEM

**We can automate ANY of these screeners for you.**

Current implementation uses:
- Relative Volume (Adrenaline Filter)
- Short Float (Squeeze Detector)  
- P/E Ratio (Value Guard)

**Want to add more filters?**
Just tell me which screeners you want, and I'll code them into `check_trading_rules()`.

Examples:
```python
# Add Insider Buying Filter
if insider_trans > 0 and insider_value > 1_000_000:
    logger.info("🔥 Insider Buying Detected")
    
# Add PEG Filter  
if peg < 1.0 and eps_growth > 20:
    logger.info("💎 Value Growth Stock")
    
# Add Pattern Filter
if pattern == "Ascending Triangle":
    logger.info("📈 Bullish Breakout Setup")
```

**Your system is ready. Which screeners should we activate?**

---

## CUSTOM FILTER CATEGORIES

When building your own custom screener, you can filter by these categories:

### 1. **DESCRIPTIVE FILTERS**
- Exchange (NYSE, NASDAQ, AMEX)
- Index (S\u0026P 500, DJIA, Nasdaq 100)
- Sector (Technology, Healthcare, Finance, etc.)
- Industry (280+ industries)
- Country (USA, China, UK, etc.)
- Market Cap (Mega >$200B, Large >$10B, Mid $2-10B, Small $300M-2B, Micro <$300M, Nano <$50M)
- Dividend Yield ranges
- Float (shares available for trading)
- Optionable/Shortable
- IPO Date

### 2. **FUNDAMENTAL FILTERS**
- **Valuation**: P/E, Forward P/E, PEG, P/S, P/B, P/C, P/FCF
- **Profitability**: Profit Margin, Operating Margin, Gross Margin, ROA, ROE, ROI
- **Growth**: EPS growth (this Y, next Y, past 5Y, next 5Y), Sales growth Q/Q, EPS Q/Q
- **Dividends**: Dividend Yield %, Payout Ratio
- **Financial Health**: Quick Ratio, Current Ratio, Debt/Equity, LT Debt/Equity
- **Performance**: Price performance (Week, Month, Quarter, Half, Year, YTD)
- **Analysts**: Recommendation (1.0=Strong Buy → 5.0=Sell)
- **Ownership**: Insider Own %, Insider Trans %, Inst Own %, Inst Trans %
- **Company Size**: Employees, Income, Sales

### 3. **TECHNICAL FILTERS**
- **Price**: Absolute price, Price vs 52W High/Low
- **Volume**: Current Volume, Relative Volume, Avg Volume (3M)
- **Volatility**: Week %, Month %, ATR
- **Moving Averages**: SMA20, SMA50, SMA200, SMA200 (distance from)
- **Momentum**: RSI(14), Change %, Change from Open %
- **Trend Patterns**: 50+ chart patterns (wedges, channels, H\u0026S, etc.)
- **Candlestick Patterns**: (if available on paid version)
- **Gap**: Gap Up/Down %
- **20-Day High/Low**: Distance from recent extremes
- **Beta**: Volatility vs market
- **Average True Range (ATR)**
- **Earnings Date**: Days until next earnings

### 4. **SIGNALS (Chart Pattern Recognition)**
All the technical patterns auto-detected:
- Support/Resistance levels
- Trendline breaks
- Channel formations
- Wedge patterns
- Triangle patterns
- Head \u0026 Shoulders
- Double/Multiple tops/bottoms

---

## VIEWS (Data Display Options)

Once you've filtered, you can view results in different formats:

1. **Overview** (v=111) - Basic ticker, price, change, volume
2. **Valuation** (v=121) - All valuation ratios
3. **Financial** (v=161) - Profitability, margins
4. **Ownership** (v=131) - Insider/Institutional holdings
5. **Performance** (v=141) - Historical returns
6. **Technical** (v=171) - RSI, volatility, beta, ATR
7. **Charts** - Visual screener with mini-charts

---

## HOW TO USE IN YOUR ALGO

You can combine these screeners programmatically:

```python
# Example: High volume momentum stocks with insider buying
filters = {
    'Relative Volume': 'Over 2',
    'Change': 'Up 5%',
    'Insider Trans': 'Very Positive',
    'RSI (14)': 'Overbought (70)'
}
df = finviz_svc.get_screener_results(filters_dict=filters)
```

**We can automate ANY of these 50+ preset screeners in your trading system.**

Which screeners are most valuable for your strategy?
