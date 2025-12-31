
from abc import ABC, abstractmethod
import pandas as pd
from typing import Dict, Any

class BaseStrategy(ABC):
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config

    @abstractmethod
    def analyze(self, symbol: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze the provided dataframe and return a signal.
        Return format:
        {
            "signal": "BUY" | "SELL" | "HOLD",
            "confidence": float (0.0 - 1.0),
            "metadata": { ... }
        }
        """
        pass
