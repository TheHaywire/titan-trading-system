import MetaTrader5 as mt5
import logging
import time
from titan_system.execution.trade_manager import TradeManager
from titan_system.execution.mt5_executor import MT5Executor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Titan.TestTM")

def test_trade_management():
    print("\n" + "="*80)
    print("   TITAN TRADE MANAGEMENT TEST: RISK-TO-ZERO VERIFICATION")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ MT5 Initialization failed.")
        return

    executor = MT5Executor()
    tm = TradeManager(be_threshold_pips=1) # Set very low for testing
    
    print("\n[STEP 1] Checking for active trades...")
    positions = mt5.positions_get()
    
    if not positions:
        print("🔍 No active trades found. Please open a small trade on GOLD or EURUSD manually to test.")
        print("   The bot will only manage trades with Magic Number 234001, but for this test,")
        print("   I will temporarily bypass the magic number check.")
    
    # Bypass magic number check for testing
    def patched_monitor(self):
        positions = mt5.positions_get()
        if not positions: return
        for pos in positions:
            print(f"  Processing Position: {pos.symbol} (#{pos.ticket})")
            # State check SL position
            is_already_be = False
            if pos.type == mt5.POSITION_TYPE_BUY:
                if pos.sl >= pos.price_open: is_already_be = True
            else:
                if pos.sl != 0 and pos.sl <= pos.price_open: is_already_be = True
            
            if is_already_be:
                print(f"  [SKIPPED] #{pos.ticket} is already de-risked.")
                continue
                
            self.check_de_risk(pos)

    # Apply patch
    import types
    tm.monitor_active_trades = types.MethodType(patched_monitor, tm)
    
    print("\n[STEP 2] Running 10-second monitoring loop...")
    for _ in range(10):
        tm.monitor_active_trades()
        time.sleep(1)

    print("\n[FINISH] Test complete. Check MT5 for changed SL and Partial TP deals.")
    print("="*80)
    mt5.shutdown()

if __name__ == "__main__":
    test_trade_management()
