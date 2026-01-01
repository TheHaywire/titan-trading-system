"""
Institutional Audit Trail (EPIC-11)
Logs system events with NTP-synchronized timestamps to ensure
compliance with high-frequency trading standards.
"""

import logging
import ntplib
import time
from datetime import datetime
import os

logger = logging.getLogger("Titan.Audit")

class AuditTrail:
    def __init__(self, log_file="data/audit_trail.log"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        self.ntp_client = ntplib.NTPClient()
        self.offset = 0
        self.sync_time()

    def sync_time(self):
        """Syncs local clock with NTP pool for microsecond accuracy."""
        try:
            response = self.ntp_client.request('pool.ntp.org', version=3)
            self.offset = response.offset
            logger.info(f"🕒 NTP Time Sync'd. Offset: {self.offset:.4f}s")
        except:
            logger.warning("⚠️ NTP Sync Failed. Using local system time.")

    def log_event(self, category, message, data=None):
        """Logs a high-fidelity event to the audit trail."""
        ntp_now = time.time() + self.offset
        ts = datetime.fromtimestamp(ntp_now).strftime('%Y-%m-%d %H:%M:%S.%f')
        
        entry = f"[{ts}] [{category}] {message}"
        if data:
            entry += f" | DATA: {data}"
            
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
            
        logger.info(f"📊 Audit: {message}")

if __name__ == "__main__":
    audit = AuditTrail()
    audit.log_event("STRATEGY", "Signal Triggered: BUY EURUSD", {"price": 1.0850, "confidence": 0.85})
