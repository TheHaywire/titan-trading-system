"""Export news and calendar to markdown doc"""
from finvizfinance.news import News
from finvizfinance.calendar import Calendar
from datetime import datetime

output = []
output.append("# Economic Calendar & News Report")
output.append(f"\n> Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
output.append("")
output.append("---")

# Fetch news
output.append("\n## Latest Market News (Finviz)")
output.append("")
try:
    n = News()
    data = n.get_news()
    news_df = data.get('news')
    
    if news_df is not None and not news_df.empty:
        output.append(f"**Found {len(news_df)} news items**")
        output.append("")
        output.append("| Time | Headline | Source |")
        output.append("|------|----------|--------|")
        
        for i, row in news_df.head(30).iterrows():
            time = row.get('Date', '')
            title = row.get('Title', '')[:60]
            source = row.get('Source', '')
            output.append(f"| {time} | {title}... | {source} |")
    else:
        output.append("*No news data available*")
except Exception as e:
    output.append(f"*Error fetching news: {e}*")

# Fetch calendar
output.append("\n---")
output.append("\n## Economic Calendar (Finviz)")
output.append("")
try:
    c = Calendar()
    cal_df = c.calendar()
    
    if cal_df is not None and not cal_df.empty:
        output.append(f"**Found {len(cal_df)} events**")
        output.append("")
        output.append("| Date | Time | Event | Actual | Expected | Prior |")
        output.append("|------|------|-------|--------|----------|-------|")
        
        for i, row in cal_df.head(20).iterrows():
            date = row.get('Date', '')
            time = row.get('Time', '')
            event = row.get('Release', '')[:40]
            actual = row.get('Actual', '')
            expected = row.get('Expected', '')
            prior = row.get('Prior', '')
            output.append(f"| {date} | {time} | {event} | {actual} | {expected} | {prior} |")
    else:
        output.append("*Calendar empty (off-hours/weekend)*")
except Exception as e:
    output.append(f"*Error fetching calendar: {e}*")

# Trading implications
output.append("\n---")
output.append("\n## Pre-Trade Check Logic")
output.append("")
output.append("The `economic_calendar.py` module checks for high-impact events:")
output.append("")
output.append("| Event Type | Blackout Window |")
output.append("|------------|-----------------|")
output.append("| NFP / Nonfarm Payrolls | +-30 minutes |")
output.append("| FOMC / Interest Rate | +-60 minutes |")
output.append("| CPI / Core CPI | +-15 minutes |")
output.append("| GDP / PPI | +-15 minutes |")
output.append("| Retail Sales | +-10 minutes |")
output.append("| PMI / ISM | +-10 minutes |")

output.append("\n### Usage in Trading Bot:")
output.append("```python")
output.append("from titan_system.core.economic_calendar import pre_trade_check")
output.append("")
output.append("check = pre_trade_check()")
output.append("if not check['safe']:")
output.append("    print(f'SKIP: {check[\"reason\"]}')")
output.append("```")

# Save
with open("docs/ECONOMIC_CALENDAR_REPORT.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

print("Report saved to docs/ECONOMIC_CALENDAR_REPORT.md")
print(f"News items: {len(news_df) if 'news_df' in dir() and news_df is not None else 0}")
