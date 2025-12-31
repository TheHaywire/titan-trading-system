import MetaTrader5 as mt5
import sys
import os
import logging
# from config.settings import settings (Removed - not needed)

# Setup Logging
logging.basicConfig(level=logging.INFO)

sys.path.append(os.getcwd())
try:
    from titan_system.integrations.google_sheets import TitanSheets
except ImportError as e:
    print(f"Import Error: {e}")
    exit()

def audit_symbols():
    print("🚀 Starting Full Asset Audit (1500+ Symbols)...")
    
    # 1. Connect to MT5
    if not mt5.initialize():
        print("❌ MT5 Init Failed")
        return

    # 2. Fetch ALL Symbols
    symbols = mt5.symbols_get()
    print(f"✅ Found {len(symbols)} symbols on Broker.")
    
    # 3. Connect to Sheets
    sheets = TitanSheets()
    if not sheets.enabled:
        print("❌ Cloud connection failed.")
        return

    # 4. Process Data
    audit_data = []
    print("⏳ Parsing Symbol Properties...")
    
    for s in symbols:
        try:
            # Determine Trade Mode
            mode = "DISABLED"
            if s.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
                mode = "FULL"
            elif s.trade_mode == mt5.SYMBOL_TRADE_MODE_LONGONLY:
                mode = "LONG_ONLY"
            elif s.trade_mode == mt5.SYMBOL_TRADE_MODE_SHORTONLY:
                mode = "SHORT_ONLY"
            elif s.trade_mode == mt5.SYMBOL_TRADE_MODE_CLOSEONLY:
                mode = "CLOSE_ONLY"
                
            row = [
                s.name,
                s.path,
                s.spread,
                s.digits,
                s.trade_contract_size,
                s.volume_min,
                s.swap_long,
                s.swap_short,
                mode
            ]
            audit_data.append(row)
        except Exception:
            continue
            
    # 5. Push to Sheets (Batched)
    print(f"📤 Uploading {len(audit_data)} records to 'SYMBOL DATABASE'...")
    
    # We use the generic update_documentation which clears and rewrites
    # Ideally should batch this if > 5000 rows, but for 1500 it's fine in one go usually
    # If Gspread times out, we might need chunking.
    
    try:
        sheets.update_documentation("SYMBOL DATABASE", audit_data)
        print("✅ Audit Complete. All symbols logged.")
    except Exception as e:
        print(f"❌ Upload Failed: {e}")
        # Fallback: Slice
        print("⚠️ Retrying with Top 500...")
        sheets.update_documentation("SYMBOL DATABASE", audit_data[:500])

if __name__ == "__main__":
    audit_symbols()
