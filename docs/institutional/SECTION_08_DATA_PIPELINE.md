# Section 08: Data Pipeline & Feature Engineering

**Owner**: Data Team  
**Status**: 📋 Pending (30%)  
**Last Updated**: 2026-01-01

---

## 🎯 Objective

Build a robust data pipeline that acquires, validates, and transforms market data into features for strategy signals. Ensure data integrity through quarantine and alerting mechanisms.

---

## 1. Data Sources

### Primary: MT5 Market Data
- **OHLCV Bars**: 1M, 5M, 15M, 30M, H1, H4, D1
- **Tick Data**: Bid, ask, last, volume
- **Depth of Market**: Level II pricing (if available)

### Secondary: Economic Calendar
- **High-Impact Events**: Interest rate decisions, NFP, GDP, CPI
- **News Feed**: Real-time headlines (requires integration)

### Tertiary: Sentiment Data
- **Twitter/X**: crypto sentiment, hashtag trends
- **Fear & Greed Index**: Market sentiment indicator
- **COT Reports**: Commitment of Traders (futures positioning)

---

## 2. Feature Store Design

### Feature Categories

#### Technical Features
- **Trend**: SMA 20/50/200, EMA, MACD
- **Momentum**: RSI, Stochastic, CCI
- **Volatility**: ATR, Bollinger Bands, Keltner Channels
- **Volume**: OBV, VWAP, Volume MA

#### Microstructure Features
- **Order Flow**: Bid/ask imbalance, tick direction
- **Spread**: Current vs average spread
- **Liquidity**: Depth at best bid/offer

#### Cross-Asset Features
- **Correlations**: EURUSD vs DXY, Gold vs USD
- **Intermarket**: S&P 500 vs VIX
- **Currency Strength**: Index of major currencies

#### Regime Features
- **Volatility Regime**: Low/Medium/High (based on ATR percentile)
- **Trend Regime**: Strong Up/Weak Up/Ranging/Weak Down/Strong Down
- **Session**: Asian/London/NY/Overlap

---

## 3. Data Acquisition Schedule

```python
# Real-time data (continuous)
- Tick data: Subscribe to symbols, stream to buffer
- OHLCV updates: On bar close events

# Scheduled data (periodic)
- Economic calendar: Daily at 00:00 UTC
- COT reports: Weekly (Fridays)
- Sentiment feeds: Every 15 minutes

# Historical data (one-time/on-demand)
- Backfill missing bars
- Download additional symbols
```

---

## 4. Data Integrity Checks

### Validation Rules

```python
def validate_ohlcv_bar(bar):
    """Check bar data integrity."""
    issues = []
    
    # Rule 1: OHLCV consistency
    if not (bar['low'] <= bar['open'] <= bar['high']):
        issues.append("Open outside High-Low range")
    
    if not (bar['low'] <= bar['close'] <= bar['high']):
        issues.append("Close outside High-Low range")
    
    # Rule 2: Outlier detection (>10x ATR move)
    atr_20 = calculate_atr(symbol, 20)
    bar_range = bar['high'] - bar['low']
    
    if bar_range > 10 * atr_20:
        issues.append(f"Abnormal range: {bar_range:.2f} (10x ATR)")
    
    # Rule 3: Zero volume (suspicious)
    if bar['tick_volume'] == 0:
        issues.append("Zero tick volume")
    
    # Rule 4: Timestamp sequence
    if bar['time'] <= get_last_bar_time():
        issues.append("Timestamp not sequential")
    
    return issues

def quarantine_bad_data(bar, issues):
    """Isolate suspicious data."""
    logger.error(f"Data quarantined: {bar['symbol']} {bar['time']} - {issues}")
    
    # Save to quarantine DB
    db.execute("""
        INSERT INTO quarantine (symbol, timestamp, issues, raw_data)
        VALUES (?, ?, ?, ?)
    """, (bar['symbol'], bar['time'], json.dumps(issues), json.dumps(bar)))
    
    # Send alert
    send_alert(f"Data integrity issue: {bar['symbol']}")
```

---

## 5. Missing Data Detection

```python
def detect_missing_bars(symbol, timeframe, start_date, end_date):
    """Find gaps in historical data."""
    
    # Get all bars
    bars = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)
    
    # Expected bar times (based on timeframe)
    bar_interval = get_timeframe_seconds(timeframe)
    expected_times = pd.date_range(
        start=start_date, end=end_date, freq=f'{bar_interval}S'
    )
    
    # Actual bar times
    actual_times = pd.to_datetime(bars['time'], unit='s')
    
    # Find missing
    missing = set(expected_times) - set(actual_times)
    
    if missing:
        logger.warning(f"Missing {len(missing)} bars for {symbol}")
        # Trigger backfill
        backfill_missing_data(symbol, timeframe, list(missing))
    
    return list(missing)
```

---

## 6. Feature Calculation Pipeline

```python
class FeatureEngine:
    """Transform raw OHLCV into features."""
    
    def __init__(self, symbol, timeframe):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data = self._load_data()
    
    def compute_all_features(self):
        """Calculate all features."""
        
        # Technical indicators
        self.data['sma_20'] = self.data['close'].rolling(20).mean()
        self.data['sma_50'] = self.data['close'].rolling(50).mean()
        self.data['sma_200'] = self.data['close'].rolling(200).mean()
        
        self.data['rsi_14'] = self._calculate_rsi(14)
        self.data['atr_14'] = self._calculate_atr(14)
        
        # Bollinger Bands
        self.data['bb_upper'], self.data['bb_lower'] = self._calculate_bb(20, 2.0)
        
        # Volume features
        self.data['volume_ma_20'] = self.data['tick_volume'].rolling(20).mean()
        self.data['volume_spike'] = self.data['tick_volume'] > self.data['volume_ma_20'] * 1.5
        
        # Regime classification
        self.data['volatility_regime'] = self._classify_volatility()
        self.data['trend_regime'] = self._classify_trend()
        
        return self.data
    
    def _classify_volatility(self):
        """Classify volatility regime."""
        atr_percentile = self.data['atr_14'].rolling(100).rank(pct=True)
        
        conditions = [
            atr_percentile < 0.33,
            atr_percentile < 0.67,
            atr_percentile >= 0.67
        ]
        choices = ['LOW', 'MEDIUM', 'HIGH']
        
        return np.select(conditions, choices, default='MEDIUM')
```

**Output**: Feature-rich DataFrame ready for strategy signals

---

## 📚 Cross-References

### Data Sources
- **MT5 Data**: Copy rates/ticks functions
- **Economic Calendar**: https://www.mql5.com/en/economic-calendar
- **COT Reports**: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm

### Titan System
- **Feature Engine**: `titan_system/data/feature_engine.py` (to be created)
- **Data Validation**: `titan_system/data/validator.py` (to be created)

---

## ✅ Validation Checklist

- [ ] Data source catalog complete
- [ ] Feature store designed
- [ ] Data integrity checks implemented
- [ ] Missing bar detection automated
- [ ] Quarantine mechanism tested
- [ ] Feature calculation pipeline built

---

**Status**: Design complete | Implementation 30%
