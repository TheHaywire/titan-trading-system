# ORB Multi-Session Backtest Results

**Generated:** 2025-12-29 17:28:46

## Strategy Logic

```
ORB = First M15 candle after session open
BUY = Close > ORB_High AND Close > VWAP
SELL = Close < ORB_Low AND Close < VWAP
Stop Loss = ORB opposite side - (0.5 × ATR)
Take Profit = 2:1 Risk-Reward
```

## Session Times (UTC)

| Session | Open Time |
|---------|----------|
| London | 08:00 |
| Newyork | 13:00 |
| Tokyo | 00:00 |
| Sydney | 22:00 |

## Full Results

| Category | Symbol | Session | Trades | Win Rate | PF |
|----------|--------|---------|--------|----------|----|
| forex | EURUSD | london | 21 | 38.1% | 1.09 |
| forex | EURUSD | newyork | 29 | 48.3% | 1.42 |
| forex | EURUSD | tokyo | 26 | 53.8% | 1.63 |
| forex | EURUSD | sydney | 13 | 15.4% | 0.23 |
| forex | GBPUSD | london | 24 | 37.5% | 1.08 |
| forex | GBPUSD | newyork | 28 | 46.4% | 1.52 |
| forex | GBPUSD | tokyo | 25 | 40.0% | 0.98 |
| forex | GBPUSD | sydney | 12 | 33.3% | 0.89 |
| forex | USDJPY | london | 24 | 50.0% | 1.67 |
| forex | USDJPY | newyork | 28 | 46.4% | 1.54 |
| forex | USDJPY | tokyo | 24 | 25.0% | 0.37 |
| forex | USDJPY | sydney | 21 | 14.3% | 0.22 |
| forex | USDCHF | london | 25 | 48.0% | 2.34 |
| forex | USDCHF | newyork | 30 | 53.3% | 2.28 |
| forex | USDCHF | tokyo | 18 | 33.3% | 0.66 |
| forex | USDCHF | sydney | 18 | 22.2% | 0.40 |
| forex | AUDUSD | london | 26 | 42.3% | 1.15 |
| forex | AUDUSD | newyork | 29 | 37.9% | 0.84 |
| forex | AUDUSD | tokyo | 24 | 54.2% | 1.05 |
| forex | AUDUSD | sydney | 18 | 27.8% | 0.75 |
| forex | NZDUSD | london | 25 | 36.0% | 0.92 |
| forex | NZDUSD | newyork | 29 | 41.4% | 0.97 |
| forex | NZDUSD | tokyo | 26 | 53.8% | 1.67 |
| forex | NZDUSD | sydney | 15 | 33.3% | 1.02 |
| forex | USDCAD | london | 25 | 36.0% | 0.89 |
| forex | USDCAD | newyork | 31 | 51.6% | 2.03 |
| forex | USDCAD | tokyo | 16 | 37.5% | 0.41 |
| forex | USDCAD | sydney | 17 | 11.8% | 0.23 |
| forex | EURGBP | london | 25 | 40.0% | 1.05 |
| forex | EURGBP | newyork | 28 | 32.1% | 0.54 |
| forex | EURGBP | tokyo | 8 | 37.5% | 0.45 |
| forex | EURGBP | sydney | 21 | 42.9% | 0.94 |
| forex | EURJPY | london | 29 | 51.7% | 1.65 |
| forex | EURJPY | newyork | 27 | 40.7% | 0.91 |
| forex | EURJPY | tokyo | 26 | 38.5% | 0.67 |
| forex | EURJPY | sydney | 18 | 11.1% | 0.16 |
| forex | GBPJPY | london | 29 | 58.6% | 1.97 |
| forex | GBPJPY | newyork | 27 | 51.9% | 1.40 |
| forex | GBPJPY | tokyo | 23 | 43.5% | 0.98 |
| forex | GBPJPY | sydney | 16 | 18.8% | 0.45 |
| forex | AUDJPY | london | 28 | 53.6% | 1.95 |
| forex | AUDJPY | newyork | 27 | 51.9% | 1.97 |
| forex | AUDJPY | tokyo | 27 | 37.0% | 0.85 |
| forex | AUDJPY | sydney | 17 | 11.8% | 0.31 |
| forex | EURAUD | london | 25 | 28.0% | 0.48 |
| forex | EURAUD | newyork | 27 | 37.0% | 0.56 |
| forex | EURAUD | tokyo | 19 | 52.6% | 1.06 |
| forex | EURAUD | sydney | 21 | 38.1% | 0.82 |
| forex | EURCHF | london | 30 | 33.3% | 1.00 |
| forex | EURCHF | newyork | 24 | 29.2% | 0.68 |
| forex | EURCHF | tokyo | 23 | 52.2% | 0.51 |
| forex | EURCHF | sydney | 18 | 16.7% | 0.19 |
| forex | GBPCHF | london | 30 | 36.7% | 0.92 |
| forex | GBPCHF | newyork | 26 | 42.3% | 1.17 |
| forex | GBPCHF | tokyo | 23 | 52.2% | 1.03 |
| forex | GBPCHF | sydney | 16 | 12.5% | 0.13 |
| forex | EURCAD | london | 27 | 37.0% | 0.94 |
| forex | EURCAD | newyork | 29 | 37.9% | 0.71 |
| forex | EURCAD | tokyo | 11 | 54.5% | 1.18 |
| forex | EURCAD | sydney | 18 | 22.2% | 0.20 |
| forex | GBPCAD | london | 25 | 32.0% | 0.99 |
| forex | GBPCAD | newyork | 28 | 28.6% | 0.38 |
| forex | GBPCAD | tokyo | 15 | 53.3% | 1.98 |
| forex | GBPCAD | sydney | 20 | 15.0% | 0.26 |
| forex | AUDCAD | london | 23 | 21.7% | 0.38 |
| forex | AUDCAD | newyork | 26 | 11.5% | 0.19 |
| forex | AUDCAD | tokyo | 25 | 48.0% | 1.19 |
| forex | AUDCAD | sydney | 20 | 25.0% | 0.58 |
| forex | NZDJPY | london | 25 | 48.0% | 1.65 |
| forex | NZDJPY | newyork | 27 | 51.9% | 1.82 |
| forex | NZDJPY | tokyo | 27 | 33.3% | 0.90 |
| forex | NZDJPY | sydney | 21 | 14.3% | 0.34 |
| forex | CHFJPY | london | 27 | 37.0% | 1.15 |
| forex | CHFJPY | newyork | 28 | 46.4% | 1.06 |
| forex | CHFJPY | tokyo | 17 | 35.3% | 0.69 |
| forex | CHFJPY | sydney | 20 | 10.0% | 0.13 |
| forex | CADJPY | london | 27 | 55.6% | 2.39 |
| forex | CADJPY | newyork | 26 | 50.0% | 1.62 |
| forex | CADJPY | tokyo | 21 | 23.8% | 0.23 |
| forex | CADJPY | sydney | 16 | 12.5% | 0.22 |
| forex | EURNZD | london | 26 | 38.5% | 0.81 |
| forex | EURNZD | newyork | 27 | 37.0% | 0.90 |
| forex | EURNZD | tokyo | 19 | 47.4% | 1.48 |
| forex | EURNZD | sydney | 20 | 40.0% | 1.04 |
| forex | GBPNZD | london | 27 | 37.0% | 0.71 |
| forex | GBPNZD | newyork | 28 | 28.6% | 0.63 |
| forex | GBPNZD | tokyo | 19 | 47.4% | 1.21 |
| forex | GBPNZD | sydney | 19 | 36.8% | 0.95 |
| forex | AUDNZD | london | 23 | 21.7% | 0.35 |
| forex | AUDNZD | newyork | 27 | 29.6% | 0.64 |
| forex | AUDNZD | tokyo | 19 | 47.4% | 0.75 |
| forex | AUDNZD | sydney | 21 | 28.6% | 0.71 |
| forex | NZDCAD | london | 22 | 31.8% | 0.60 |
| forex | NZDCAD | newyork | 25 | 24.0% | 0.44 |
| forex | NZDCAD | tokyo | 21 | 61.9% | 1.83 |
| forex | NZDCAD | sydney | 18 | 33.3% | 0.88 |
| forex | GBPAUD | london | 26 | 34.6% | 0.92 |
| forex | GBPAUD | newyork | 26 | 23.1% | 0.41 |
| forex | GBPAUD | tokyo | 15 | 40.0% | 0.86 |
| forex | GBPAUD | sydney | 19 | 31.6% | 0.78 |
| commodity | OILCash | london | 26 | 46.2% | 2.06 |
| commodity | OILCash | newyork | 25 | 40.0% | 1.08 |
| commodity | OILCash | sydney | 19 | 42.1% | 1.12 |
| commodity | BRENTCash | london | 29 | 34.5% | 1.25 |
| commodity | BRENTCash | newyork | 28 | 46.4% | 1.74 |
| commodity | BRENTCash | tokyo | 23 | 43.5% | 0.80 |
| commodity | BRENTCash | sydney | 18 | 44.4% | 1.17 |
| commodity | GOLD | london | 22 | 40.9% | 0.99 |
| commodity | GOLD | newyork | 28 | 32.1% | 1.10 |
| commodity | GOLD | sydney | 20 | 45.0% | 0.94 |
| index | US30Cash | london | 27 | 51.9% | 2.05 |
| index | US30Cash | newyork | 31 | 45.2% | 1.83 |
| index | US30Cash | sydney | 13 | 53.8% | 0.86 |
| index | US100Cash | london | 29 | 17.2% | 0.39 |
| index | US100Cash | newyork | 30 | 36.7% | 1.52 |
| index | US100Cash | sydney | 17 | 52.9% | 2.17 |
| index | US500Cash | london | 29 | 20.7% | 0.61 |
| index | US500Cash | newyork | 32 | 40.6% | 1.33 |
| index | US500Cash | sydney | 14 | 42.9% | 1.30 |
| index | US2000Cash | london | 28 | 50.0% | 1.97 |
| index | US2000Cash | newyork | 29 | 34.5% | 0.81 |
| index | US2000Cash | sydney | 11 | 27.3% | 0.49 |
| index | UK100Cash | london | 32 | 28.1% | 0.65 |
| index | UK100Cash | newyork | 26 | 26.9% | 0.42 |
| index | UK100Cash | sydney | 18 | 38.9% | 0.48 |
| crypto | BTCUSD | london | 24 | 20.8% | 0.35 |
| crypto | BTCUSD | newyork | 24 | 50.0% | 0.81 |
| crypto | BTCUSD | tokyo | 25 | 36.0% | 0.85 |
| crypto | BTCUSD | sydney | 20 | 30.0% | 0.54 |
| crypto | ETHUSD | london | 24 | 29.2% | 0.59 |
| crypto | ETHUSD | newyork | 24 | 45.8% | 2.74 |
| crypto | ETHUSD | tokyo | 21 | 33.3% | 0.66 |
| crypto | ETHUSD | sydney | 19 | 42.1% | 1.21 |
| crypto | XRPUSD | london | 24 | 29.2% | 0.62 |
| crypto | XRPUSD | newyork | 24 | 45.8% | 2.11 |
| crypto | XRPUSD | tokyo | 20 | 40.0% | 1.35 |
| crypto | XRPUSD | sydney | 22 | 50.0% | 1.51 |
| crypto | LTCUSD | london | 25 | 36.0% | 0.75 |
| crypto | LTCUSD | newyork | 24 | 54.2% | 2.58 |
| crypto | LTCUSD | tokyo | 18 | 33.3% | 0.74 |
| crypto | LTCUSD | sydney | 25 | 36.0% | 0.74 |
| crypto | ADAUSD | london | 24 | 20.8% | 0.48 |
| crypto | ADAUSD | newyork | 21 | 71.4% | 3.88 |
| crypto | ADAUSD | tokyo | 20 | 45.0% | 1.28 |
| crypto | ADAUSD | sydney | 20 | 40.0% | 1.02 |
| crypto | SOLUSD | london | 20 | 30.0% | 0.83 |
| crypto | SOLUSD | newyork | 23 | 43.5% | 1.99 |
| crypto | SOLUSD | tokyo | 19 | 47.4% | 0.92 |
| crypto | SOLUSD | sydney | 18 | 38.9% | 1.13 |
| crypto | BTCEUR | london | 23 | 26.1% | 0.60 |
| crypto | BTCEUR | newyork | 25 | 48.0% | 1.32 |
| crypto | BTCEUR | tokyo | 23 | 39.1% | 1.07 |
| crypto | BTCEUR | sydney | 20 | 35.0% | 0.84 |
