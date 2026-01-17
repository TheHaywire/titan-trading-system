"""Quick test of economic calendar and news"""
from finvizfinance.news import News
from finvizfinance.calendar import Calendar
import pandas as pd

print("=" * 70)
print("FINVIZ ECONOMIC CALENDAR & NEWS TEST")
print("=" * 70)

# Test news
print("\n--- MARKET NEWS ---")
try:
    n = News()
    data = n.get_news()
    news_df = pd.DataFrame(data['news'])
    print(f"Found {len(news_df)} news items")
    print("\nLatest Headlines:")
    for i, row in news_df.head(10).iterrows():
        title = row.get('Title', str(row.iloc[1]) if len(row) > 1 else 'No title')
        date = row.get('Date', str(row.iloc[0]) if len(row) > 0 else 'No date')
        print(f"  [{date}] {title[:65]}...")
except Exception as e:
    print(f"News error: {e}")

# Test calendar
print("\n--- ECONOMIC CALENDAR ---")
try:
    c = Calendar()
    cal_df = c.calendar()
    if cal_df.empty:
        print("Calendar empty (likely weekend/market closed)")
    else:
        print(f"Found {len(cal_df)} events")
        print(cal_df.head(10))
except Exception as e:
    print(f"Calendar error: {e}")

print("\n" + "=" * 70)
print("VALIDATION COMPLETE")
