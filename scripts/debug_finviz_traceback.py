import traceback
from finvizfinance.screener.overview import Overview
import logging

logging.basicConfig(level=logging.INFO)

print("Starting Traceback Diagnostic for Finviz Screener...")
try:
    foverview = Overview()
    # No filters, just plain call
    df = foverview.screener_view()
    print("Success!")
except Exception as e:
    print("--- TRACEBACK START ---")
    traceback.print_exc()
    print("--- TRACEBACK END ---")
