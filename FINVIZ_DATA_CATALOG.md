# TITAN INTEL: THE FULL FINVIZ ARSENAL (70+ METRICS)

You asked for **EVERYTHING**. No summaries. Here is the full list of raw data points we can extract and use in the trading algo.

## 1. VALUATION (Is it cheap?)
1.  **Index**: (S&P500, DJIA, etc.)
2.  **P/E**: Price to Earnings Ratio
3.  **EPS (ttm)**: Earnings Per Share (Trailing 12 Months)
4.  **Insider Own**: % Owned by Insiders
5.  **Shs Outstand**: Total Shares Outstanding
6.  **Perf Week**: Performance this week
7.  **Market Cap**: Total Dollar Value
8.  **Forward P/E**: Forecasted P/E
9.  **EPS next Y**: Forecasted EPS Growth Next Year
10. **Insider Trans**: Recent Insider Buying/Selling %
11. **Shs Float**: Tradable Shares (Volatility Fuel)
12. **Perf Month**: Performance this month
13. **Income**: Net Profit
14. **PEG**: Price/Earnings to Growth
15. **EPS next Q**: Forecasted EPS Next Quarter
16. **Inst Own**: % Owned by Institutions
17. **Short Float**: % of Float Sold Short (Squeeze Fuel)
18. **Perf Quarter**: Performance this quarter
19. **Sales**: Total Revenue
20. **P/S**: Price to Sales Ratio
21. **EPS this Y**: EPS Growth This Year
22. **Inst Trans**: Institutional Buying/Selling %
23. **Short Ratio**: Days to Cover Shorts
24. **Perf Half Y**: Performance this half-year
25. **Book/sh**: Book Value per Share
26. **P/B**: Price to Book Ratio
27. **EPS next 5Y**: EPS Growth Forecast (5 Years)
28. **ROA**: Return on Assets
29. **Target Price**: Average Analyst Target
30. **Perf Year**: Performance this year
31. **Cash/sh**: Cash per Share
32. **P/C**: Price to Cash Ratio
33. **EPS past 5Y**: EPS Growth (Last 5 Years)
34. **ROE**: Return on Equity
35. **52W Range**: Yearly Price Range
36. **Perf YTD**: Performance Year-to-Date
37. **Dividend**: Dividend Amount
38. **P/FCF**: Price to Free Cash Flow
39. **EPS Q/Q**: EPS Growth Quarter-over-Quarter
40. **ROI**: Return on Investment
41. **52W High**: Distance from 52-Week High
42. **Beta**: Volatility relative to market
43. **Dividend %**: Dividend Yield
44. **Quick Ratio**: Liquidity (Cash/Liabilities)
45. **Sales Q/Q**: Sales Growth Quarter-over-Quarter
46. **Gross Margin**: Profit Margin (Raw)
47. **52W Low**: Distance from 52-Week Low
48. **ATR**: Average True Range (Volatility)
49. **Employees**: Number of Employees
50. **Current Ratio**: Short-term Liquidity
51. **Oper. Margin**: Operating Margin
52. **RSI (14)**: Relative Strength Index
53. **Volatility**: (Week / Month)
54. **Optionable**: Has Options?
55. **Debt/Eq**: Debt to Equity Ratio
56. **EPS this Y**: EPS Estimate for Current Year
57. **Profit Margin**: Net Profit Margin (% of Sales kept)
58. **Rel Volume**: Volume vs Average (Institutional Activity)
59. **Prev Close**: Previous Day's Close Price
60. **Shortable**: Can it be shorted?
61. **LT Debt/Eq**: Long-Term Debt to Equity
62. **Earnings**: Date of next earnings report
63. **Payout**: Dividend Payout Ratio
64. **Avg Volume**: Average Daily Volume
65. **Price**: Current Price
66. **Recom**: Analyst Recommendation (1=Buy, 5=Sell)
67. **SMA20**: Distance from 20-Day Moving Average
68. **SMA50**: Distance from 50-Day Moving Average
69. **SMA200**: Distance from 200-Day Moving Average
70. **Volume**: Today's Volume
71. **Change**: Today's % Change

## 2. NEWS & EVENTS
72. **News Headlines**: Real-time aggregated news.
73. **News Source**: (Bloomberg, Reuters, WSJ, etc.)
74. **News Date/Time**: Timestamp of news.
75. **Analyst Upgrades**: Recent rating changes.

## 3. INSIDER TRADING (The "Cheat Sheet")
76. **Insider Name**: Who bought/sold?
77. **Relationship**: CEO, CFO, Director?
78. **Date**: When did they trade?
79. **Transaction**: Buy or Sale?
80. **Cost**: Price they paid/sold at.
81. **#Shares**: How many shares?
82. **Value ($)**: Total value of transaction.
83. **#Shares Total**: How many shares they hold now.
84. **SEC Form 4**: Link to official filing.

---

**This is every single variable we have access to.**
We can build rules on ANY of these 84 data points.
Example: *"Only buy if `Insider Trans > 0` AND `Short Float > 20%` AND `RSI < 30`."*
