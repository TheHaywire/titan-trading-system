# Economic Calendar & News Report

> Generated: 2026-01-17 00:39:32

---

## Latest Market News (Finviz)

**Found 90 news items**

| Time | Headline | Source |
|------|----------|--------|
| 02:07PM | S&P 500 rises slightly Friday, heads for losing week as trad... | www.cnbc.com |
| 01:48PM | White House economic advisor floats idea of 'Trump cards’ am... | www.cnbc.com |
| 01:00PM | ChatGPT to carry adverts for some users... | www.bbc.com |
| 12:56PM | US CEOs fear economic uncertainty more than their global pee... | foxbusiness.com |
| 12:43PM | Trump to unveil home buying plan involving retirement funds... | www.bbc.com |
| 12:39PM | Trump Praises Hassett, but Casts Doubt on Making Him Fed Cha... | www.nytimes.com |
| 12:19PM | Chip stocks lift S&P 500 in volatile trading ahead of long w... | www.reuters.com |
| 12:18PM | Economist argues housing is unaffordable because the governm... | www.foxbusiness.com |
| 12:18PM | Home prices are rising and falling the most in these US citi... | foxbusiness.com |
| 12:15PM | Warsh’s chances of becoming Fed chair jump as Trump suggests... | www.marketwatch.com |
| 12:13PM | Why one economist says inflation is actually lower than we t... | www.marketwatch.com |
| 11:57AM | Powell, an Unlikely Foil, Takes on Trump... | www.nytimes.com |
| 11:50AM | Trump to Hassett: 'I actually want to keep you where you are... | finance.yahoo.com |
| 11:50AM | Trump moves to make Big Tech 'pay their own way' for surging... | finance.yahoo.com |
| 11:45AM | Warsh’s chance of scoring Fed job rise after Trump’s comment... | www.marketwatch.com |
| 11:38AM | Trump floats tariff on countries that don't support Greenlan... | finance.yahoo.com |
| 11:25AM | Stocks wobble as Trump wavers on Hassett as Fed pick... | finance.yahoo.com |
| 11:24AM | Trump's pursuit of Powell threatens to muddle Fed tea leaves... | finance.yahoo.com |
| 11:15AM | Stock Market Today: Trump Suggests Hassett Might Not Be Name... | www.wsj.com |
| 10:19AM | Coinbase CEO warns CLARITY Act could have 'dangerous' conseq... | www.foxbusiness.com |
| 10:12AM | Dow, S&P 500 turn lower; Nasdaq climbs as tech rebound gathe... | www.marketwatch.com |
| 10:00AM | Options expiration could clear path for US stock market vola... | www.reuters.com |
| 09:55AM | Grant Cardone pushes crypto-real estate hybrid as Trump team... | www.foxbusiness.com |
| 09:53AM | Trump economist Kevin Hassett: 'We're looking at one of the ... | www.foxbusiness.com |
| 09:48AM | 'Nightmare scenario': Nvidia's China woes could risk its lea... | finance.yahoo.com |
| 09:37AM | Dow, S&P 500 and Nasdaq climb as tech rebound gathers streng... | www.marketwatch.com |
| 09:00AM | Your Tax Refund Could Be Taken if You’ve Defaulted on Studen... | www.nytimes.com |
| 09:00AM | Michael Saylor’s Creative Bitcoin Strategy Isn’t Working... | www.nytimes.com |
| 09:00AM | What’s Next for Cuba, Now That Its Main Oil Supplier Is Gone... | www.nytimes.com |
| 08:56AM | Mother of Elon Musk's child sues xAI over Grok deepfakes... | www.bbc.com |

---

## Economic Calendar (Finviz)

*Calendar empty (off-hours/weekend)*

---

## Pre-Trade Check Logic

The `economic_calendar.py` module checks for high-impact events:

| Event Type | Blackout Window |
|------------|-----------------|
| NFP / Nonfarm Payrolls | +-30 minutes |
| FOMC / Interest Rate | +-60 minutes |
| CPI / Core CPI | +-15 minutes |
| GDP / PPI | +-15 minutes |
| Retail Sales | +-10 minutes |
| PMI / ISM | +-10 minutes |

### Usage in Trading Bot:
```python
from titan_system.core.economic_calendar import pre_trade_check

check = pre_trade_check()
if not check['safe']:
    print(f'SKIP: {check["reason"]}')
```