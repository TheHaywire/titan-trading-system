# Titan Portfolio Correlation Audit

This report identifies overlapping movements between assets to prevent over-exposure.

## Correlation Matrix
|        |   GOLD |   EURUSD |   BTCUSD |   GBPUSD |   USDJPY |   AUDUSD |   USDCAD |   USDCHF |
|:-------|-------:|---------:|---------:|---------:|---------:|---------:|---------:|---------:|
| GOLD   |   1    |     0.22 |     0.22 |     0.23 |    -0.05 |     0.43 |    -0.37 |    -0.13 |
| EURUSD |   0.22 |     1    |     0.07 |     0.69 |    -0.53 |     0.52 |    -0.54 |    -0.78 |
| BTCUSD |   0.22 |     0.07 |     1    |     0.11 |     0.1  |     0.35 |    -0.29 |    -0.06 |
| GBPUSD |   0.23 |     0.69 |     0.11 |     1    |    -0.45 |     0.55 |    -0.49 |    -0.56 |
| USDJPY |  -0.05 |    -0.53 |     0.1  |    -0.45 |     1    |    -0.16 |     0.25 |     0.56 |
| AUDUSD |   0.43 |     0.52 |     0.35 |     0.55 |    -0.16 |     1    |    -0.68 |    -0.29 |
| USDCAD |  -0.37 |    -0.54 |    -0.29 |    -0.49 |     0.25 |    -0.68 |     1    |     0.46 |
| USDCHF |  -0.13 |    -0.78 |    -0.06 |    -0.56 |     0.56 |    -0.29 |     0.46 |     1    |

## Risk Insights
> [!WARNING]
> High Correlation detected. Avoid trading these pairs simultaneously as it triples your risk for the same move.

**Quant Tip**: Institutional desks keep correlations below 0.6 to achieve a 'Smoother' equity curve.