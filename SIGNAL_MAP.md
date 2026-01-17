# TITAN SYSTEM: INTELLIGENCE-TO-ACTION MAP

This document maps exactly how `Finviz Intelligence` transforms into `MT5 Trade Actions`.

## 1. The "Adrenaline" Filter (Volume Validation)
**Concept**: Price moves without volume are fake.
- **Finviz Metric**: `Relative Volume`
- **Signal Logic**:
| Rel Vol | Meaning | Action |
| :--- | :--- | :--- |
| **> 1.5** | Institutional Buying | **✅ GREEN LIGHT** (Full Size) |
| **0.8 - 1.5** | Normal Activity | **⚠️ AMBER LIGHT** (Half Size) |
| **< 0.8** | Retail Noise | **❌ RED LIGHT** (No Trade) |

## 2. The "Squeeze" Detector (Sentiment)
**Concept**: High short interest fuels explosive rallies.
- **Finviz Metric**: `Short Float`
- **Signal Logic**:
| Short Float | Meaning | Action |
| :--- | :--- | :--- |
| **> 20%** | Extreme Pessimism | **🚀 ROCKET MODE** (Target +20% higher) |
| **< 5%** | Neutral | **➡️ NORMAL MODE** (Standard Targets) |

## 3. The "Value" Guard (Fundamentals)
**Concept**: Don't buy overpriced assets at the top.
- **Finviz Metric**: `P/E Ratio`
- **Signal Logic**:
| P/E Ratio | Context | Action |
| :--- | :--- | :--- |
| **> 50** | Expensive | **📉 PULLBACK ONLY** (Buy dips, don't chase breakouts) |
| **< 15** | Cheap | **📈 VALUE BUY** (Aggressive Accumulation) |

---

## 4. CONCRETE EXAMPLES

### Scenario A: GOLD (XAUUSD -> GLD)
- **MT5**: Price breaks H1 Resistance. (Technical Buy)
- **Finviz (GLD)**: Rel Vol = **0.6** (Weak).
- **DECISION**: **❌ NO TRADE**. (Likely a "Bull Trap" fakeout).

### Scenario B: SILVER (XAGUSD -> SLV)
- **MT5**: Price breaks H1 Resistance. (Technical Buy)
- **Finviz (SLV)**: Rel Vol = **2.1** (Strong) + Short Float = **8%**.
- **DECISION**: **✅ EXECUTE BUY**. (Institutional backing confirmed).

### Scenario C: NASDAQ (US100 -> QQQ)
- **MT5**: Price trending up.
- **Finviz (QQQ)**: P/E = **35** (High) + Rel Vol = **1.2** (Average).
- **DECISION**: **⚠️ HALF SIZE**. (Trend is real, but valuation is stretched).
