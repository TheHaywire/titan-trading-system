from finvizfinance.screener.overview import Overview
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting minimal screener test (no filters)...")
try:
    foverview = Overview()
    df = foverview.screener_view()
    if df is not None:
        print("Success! Pulled first 5 results:")
        print(df.head())
    else:
        print("Failed: screener_view returned None")
except Exception as e:
    logger.error(f"Error: {e}")
