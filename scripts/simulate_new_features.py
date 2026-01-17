import os
import sys
import unittest
import time
import random
import logging
from unittest.mock import MagicMock, patch

# Ensure root is in path
sys.path.append(os.getcwd())

from titan_system.core.alpha_optimizer import AlphaOptimizer
from titan_system.core.manager import TradeManager
from titan_system.db.database import Database

class TestIntegrationSuite(unittest.TestCase):
    def setUp(self):
        # Unique DB for each run to avoid file lock issues on Windows
        self.test_db = f"titan_system/db/test_titan_{random.randint(1000,9999)}.db"
        self.db = Database(self.test_db)
        
        # Mock Execution Client
        self.mock_execution = MagicMock()
        self.mock_execution.config.db_path = self.test_db
        self.mock_execution.connected = True
        
        # Initialize components
        self.alpha_opt = AlphaOptimizer()
        self.manager = TradeManager(self.mock_execution)

    def test_alpha_scaling_logic(self):
        print(f"\n--- Testing Alpha Scaling (v2.0) ---")
        
        # Scenario 1: Winning Streak
        perf_hot = {"expectancy": 600, "win_rate": 0.70, "streak": 3}
        mult_hot = self.alpha_opt.get_scaling_multiplier("GOLD", perf_hot)
        print(f"Hot Hand Multiplier: {mult_hot}x")
        self.assertGreater(mult_hot, 1.2)
        
        # Scenario 2: Drawdown Defense
        perf_norm = {"expectancy": 100, "win_rate": 0.50, "streak": 0}
        acc_dd = {"equity": 9500, "balance": 10000}
        mult_dd = self.alpha_opt.get_scaling_multiplier("GOLD", perf_norm, account_info=acc_dd)
        print(f"Drawdown Multiplier: {mult_dd}x")
        self.assertLess(mult_dd, 0.8)

    def test_adaptive_management_exit(self):
        print("\n--- Testing Adaptive Trade Management ---")
        position = MagicMock()
        position.ticket = 55555
        position.symbol = "GOLD"
        position.type = 0 # BUY
        position.profit = -10.0
        position.magic = 234000
        
        context = {"symbol": "GOLD", "bias": "BEARISH", "regime": {"current": "TREND_STRONG"}}
        
        with patch.object(self.mock_execution, 'close_position', return_value=True) as mock_close:
            self.manager._process_position(position, context)
            mock_close.assert_called_once()
            print("Adaptive Exit Triggered & Verified")

    def test_decision_ledger_recording(self):
        print("\n--- Testing Decision Ledger Recording ---")
        self.db.record_decision(
            symbol="BTCUSD",
            decision="REJECTED",
            reason="News High Risk",
            score=45.0
        )
        
        decisions = self.db.get_latest_decisions(limit=1)
        self.assertEqual(len(decisions), 1)
        print(f"Ledger Audit: Successfully recorded {decisions[0]['decision']} for {decisions[0]['symbol']}")

    def tearDown(self):
        # Force close connections
        if hasattr(self, 'db'):
            self.db.close()
            # The Database class might have other instances in its singleton cache
            # But here we just want to remove our test file
            del Database._instances[self.test_db]
        
        # Clean up file
        max_retries = 5
        for i in range(max_retries):
            try:
                if os.path.exists(self.test_db):
                    os.remove(self.test_db)
                break
            except PermissionError:
                time.sleep(0.2)

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
