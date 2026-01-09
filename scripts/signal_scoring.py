"""
Institutional Signal Scoring Module
Provides transparent, dimension-based scoring for trading setups.
"""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum

class SignalGrade(Enum):
    """Quality grade for trading setups"""
    A_PLUS = "A+"  # 9-10/10
    A = "A"        # 7-8/10
    B = "B"        # 5-6/10
    C = "C"        # 3-4/10
    D = "D"        # 1-2/10
    F = "F"        # 0/10

class TradingMode(Enum):
    """Trading style configuration"""
    SCALP = "SCALP"      # 5M-1H entries, quick trades
    INTRADAY = "INTRADAY"  # 1H-4H entries, same-day
    SWING = "SWING"      # 4H-1D entries, multi-day

@dataclass
class SignalDimensions:
    """Individual scoring dimensions"""
    trend_alignment: int = 0  # -2 to +2: HTF trend agreement
    location: int = 0         # 0 to +2: Near key S/R or fib
    momentum: int = 0         # -2 to +2: RSI, ADX, volume
    structure: int = 0        # -2 to +2: Patterns, divergence
    volatility: int = 0       # -1 to +1: ATR state (good/bad)
    
    def total(self) -> int:
        """Calculate total score"""
        return sum([
            self.trend_alignment,
            self.location,
            self.momentum,
            self.structure,
            self.volatility
        ])
    
    def to_dict(self) -> Dict[str, int]:
        """Export as dictionary"""
        return {
            'trend_alignment': self.trend_alignment,
            'location': self.location,
            'momentum': self.momentum,
            'structure': self.structure,
            'volatility': self.volatility,
            'total': self.total()
        }

@dataclass
class SignalScore:
    """Complete signal evaluation with transparent scoring"""
    symbol: str
    direction: str  # "LONG", "SHORT", "NEUTRAL"
    dimensions: SignalDimensions = field(default_factory=SignalDimensions)
    warnings: List[str] = field(default_factory=list)
    catalysts: List[str] = field(default_factory=list)
    
    def calculate_grade(self) -> SignalGrade:
        """Convert score to letter grade"""
        score = self.dimensions.total()
        if score >= 9:
            return SignalGrade.A_PLUS
        elif score >= 7:
            return SignalGrade.A
        elif score >= 5:
            return SignalGrade.B
        elif score >= 3:
            return SignalGrade.C
        elif score >= 1:
            return SignalGrade.D
        else:
            return SignalGrade.F
    
    def calculate_confidence(self) -> int:
        """Calculate confidence percentage (0-100)"""
        score = self.dimensions.total()
        max_score = 9  # Maximum possible positive score
        
        # Normalize to 0-100 scale
        if score <= 0:
            return max(0, 50 + (score * 5))  # Negative scores below 50%
        else:
            # Positive scores: 50% + scaled bonus
            return min(100, 50 + int((score / max_score) * 50))
    
    def get_quality_label(self) -> str:
        """Get human-readable quality label"""
        grade = self.calculate_grade()
        if grade in [SignalGrade.A_PLUS, SignalGrade.A]:
            return "PREMIUM"
        elif grade == SignalGrade.B:
            return "HIGH"
        elif grade == SignalGrade.C:
            return "MEDIUM"
        else:
            return "LOW"
    
    def to_dict(self) -> Dict:
        """Export complete signal as dictionary"""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'grade': self.calculate_grade().value,
            'confidence': self.calculate_confidence(),
            'quality': self.get_quality_label(),
            'score': self.dimensions.total(),
            'dimensions': self.dimensions.to_dict(),
            'catalysts': self.catalysts,
            'warnings': self.warnings
        }
    
    def __str__(self) -> str:
        """Human-readable string representation"""
        grade = self.calculate_grade()
        conf = self.calculate_confidence()
        return f"{self.symbol}: {self.direction} - Grade {grade.value} ({conf}% confidence)"

class TradingModeConfig:
    """Configuration for different trading styles"""
    
    @staticmethod
    def get_config(mode: TradingMode) -> Dict:
        """Get configuration for specific trading mode"""
        configs = {
            TradingMode.SCALP: {
                'htf_timeframes': ['1W', '1D', '4H'],      # Context only
                'ltf_timeframes': ['1H', '15M', '5M'],     # Entry triggers
                'tf_weights': {
                    '15M': 3,
                    '1H': 2,
                    '4H': 1,
                    '1D': 1,
                    '1W': 1
                },
                'stop_atr_multiplier': 1.5,
                'tp_atr_multiplier': 3.0,
                'min_rr': 2.0,
                'pattern_priority': 'LTF_FIRST',
                'max_holding_hours': 8
            },
            TradingMode.INTRADAY: {
                'htf_timeframes': ['1W', '1D', '4H'],
                'ltf_timeframes': ['4H', '1H', '15M'],
                'tf_weights': {
                    '1H': 3,
                    '4H': 2,
                    '1D': 2,
                    '15M': 1,
                    '1W': 1
                },
                'stop_atr_multiplier': 2.0,
                'tp_atr_multiplier': 4.0,
                'min_rr': 2.5,
                'pattern_priority': 'BALANCED',
                'max_holding_hours': 24
            },
            TradingMode.SWING: {
                'htf_timeframes': ['1M', '1W', '1D'],
                'ltf_timeframes': ['4H', '1H'],
                'tf_weights': {
                    '1D': 3,
                    '1W': 3,
                    '4H': 2,
                    '1H': 1,
                    '1M': 1
                },
                'stop_atr_multiplier': 3.0,
                'tp_atr_multiplier': 6.0,
                'min_rr': 3.0,
                'pattern_priority': 'HTF_FIRST',
                'max_holding_days': 7
            }
        }
        return configs.get(mode, configs[TradingMode.SCALP])
