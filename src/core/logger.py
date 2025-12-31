"""
System Logger
Standardized logging for the 'Glass Box' visibility.
"""
import logging
from datetime import datetime

class SystemLogger:
    def __init__(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler("titan.log"),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("Titan")
        
    def info(self, msg): self.logger.info(msg)
    def error(self, msg): self.logger.error(msg)
    def critical(self, msg): self.logger.critical(msg)
