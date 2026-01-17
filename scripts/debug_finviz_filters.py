from finvizfinance.screener.overview import Overview

foverview = Overview()
filters = foverview.get_filters()
print("Available filters keys:", list(filters.keys())[:20])
# Check specifically for the ones I used
print("Average Volume options:", filters.get('Average Volume'))
print("Price options:", filters.get('Price'))
