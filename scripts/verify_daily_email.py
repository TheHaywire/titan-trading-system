from daily_analyst import DailyAnalyst
import logging

# Setup logging to see output
logging.basicConfig(level=logging.INFO)

print("Starting verification of Daily Analysis Email...")
try:
    analyst = DailyAnalyst()
    # Override notifier to avoid spamming real email if needed, 
    # but user wants to see it, so we'll let it fly.
    # We might want to just print the HTML to file to verify structure locally too.
    
    # 1. Run full analysis (it includes scanning now)
    analyst.run_daily_analysis()
    
    print("\nVerification script finished. Please check your inbox.")

except Exception as e:
    print(f"Verification failed: {e}")
    import traceback
    traceback.print_exc()
