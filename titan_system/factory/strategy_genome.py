"""
STRATEGY GENOME - Universal Strategy Representation
===================================================
Defines the DNA structure for all trading strategies (manual, generated, evolved).
This enables uniform backtesting, auto-code generation, and evolution.
"""

import uuid
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from copy import deepcopy


class StrategyGenome:
    """
    Universal representation of a trading strategy.
    Think of this as the 'DNA' that can be:
    - Backtested
    - Mutated
    - Crossed-over
    - Compiled to executable code
    """
    
    # Strategy Types
    MEAN_REVERSION = "MeanReversion"
    TREND_FOLLOWING = "TrendFollowing"
    BREAKOUT = "Breakout"
    MOMENTUM = "Momentum"
    SCALPING = "Scalping"
    ARBITRAGE = "Arbitrage"
    
    def __init__(self, genome_dict: Optional[Dict] = None):
        """
        Initialize from dictionary or create blank genome.
        
        Args:
            genome_dict: Pre-defined genome structure (for loading existing strategies)
        """
        if genome_dict:
            self.genome = deepcopy(genome_dict)
            # Validate required fields
            self._validate()
        else:
            # Create new blank genome
            self.genome = self._create_blank()
    
    def _create_blank(self) -> Dict:
        """Create a minimal valid genome structure."""
        return {
            "id": str(uuid.uuid4()),
            "name": "Unnamed_Strategy",
            "type": self.MEAN_REVERSION,
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "parent_id": None,
            "generation": 0,
            
            "symbols": [],
            "timeframe": "M15",
            
            "indicators": {},
            "entry_rules": [],
            "exit_rules": {
                "tp_mult": 2.0,
                "sl_atr": 1.5,
                "trail_trigger": None,
                "breakeven_trigger": None
            },
            
            "filters": {
                "mtf_trend": False,
                "time_of_day": None,
                "volatility_max": None,
                "volume_min": None
            },
            
            "parameters": {
                "risk_per_trade": 0.01,
                "max_positions": 2,
                "max_trades_per_day": 10
            },
            
            "metadata": {
                "description": "",
                "tags": [],
                "notes": ""
            }
        }
    
    def _validate(self):
        """Validate genome has all required fields."""
        required = ["id", "name", "type", "symbols", "timeframe", "indicators", 
                    "entry_rules", "exit_rules", "parameters"]
        for field in required:
            if field not in self.genome:
                raise ValueError(f"Invalid genome: missing required field '{field}'")
    
    # ==================== ACCESSORS ====================
    
    @property
    def id(self) -> str:
        return self.genome["id"]
    
    @property
    def name(self) -> str:
        return self.genome["name"]
    
    @name.setter
    def name(self, value: str):
        self.genome["name"] = value
    
    @property
    def type(self) -> str:
        return self.genome["type"]
    
    @property
    def symbols(self) -> List[str]:
        return self.genome["symbols"]
    
    @property
    def timeframe(self) -> str:
        return self.genome["timeframe"]
    
    @property
    def indicators(self) -> Dict:
        return self.genome["indicators"]
    
    @property
    def entry_rules(self) -> List[Dict]:
        return self.genome["entry_rules"]
    
    @property
    def exit_rules(self) -> Dict:
        return self.genome["exit_rules"]
    
    @property
    def parameters(self) -> Dict:
        return self.genome["parameters"]
    
    # ==================== BUILDERS ====================
    
    def set_symbols(self, symbols: List[str]):
        """Set target symbols."""
        self.genome["symbols"] = symbols
        return self
    
    def set_timeframe(self, tf: str):
        """Set primary timeframe (e.g., 'M15', 'H1')."""
        self.genome["timeframe"] = tf
        return self
    
    def add_indicator(self, name: str, params: Dict):
        """
        Add technical indicator to the strategy.
        
        Example:
            genome.add_indicator("RSI", {"period": 14, "overbought": 70, "oversold": 30})
        """
        self.genome["indicators"][name] = params
        return self
    
    def add_entry_rule(self, condition: str, weight: float, description: str = ""):
        """
        Add entry signal rule.
        
        Args:
            condition: Boolean expression (e.g., "RSI < 30")
            weight: Contribution to final score (0.0 - 1.0)
            description: Human-readable explanation
        """
        self.genome["entry_rules"].append({
            "condition": condition,
            "weight": weight,
            "description": description
        })
        return self
    
    def set_exit_rules(self, tp_mult: float = None, sl_atr: float = None, 
                       trail_trigger: float = None, breakeven_trigger: float = None):
        """
        Set exit/trade management rules.
        
        Args:
            tp_mult: Take profit as multiple of R (e.g., 2.0 = 2:1 R:R)
            sl_atr: Stop loss as ATR multiplier
            trail_trigger: Trigger trailing stop at R multiple
            breakeven_trigger: Move SL to breakeven at R multiple
        """
        if tp_mult is not None:
            self.genome["exit_rules"]["tp_mult"] = tp_mult
        if sl_atr is not None:
            self.genome["exit_rules"]["sl_atr"] = sl_atr
        if trail_trigger is not None:
            self.genome["exit_rules"]["trail_trigger"] = trail_trigger
        if breakeven_trigger is not None:
            self.genome["exit_rules"]["breakeven_trigger"] = breakeven_trigger
        return self
    
    def set_filter(self, filter_name: str, value: Any):
        """
        Enable/configure filters.
        
        Common filters:
        - mtf_trend: Require multi-timeframe trend alignment
        - time_of_day: "London+NY", "Asian", etc.
        - volatility_max: Maximum ATR% to trade
        - volume_min: Minimum volume threshold
        """
        self.genome["filters"][filter_name] = value
        return self
    
    def set_risk_params(self, risk_per_trade: float = None, max_positions: int = None, 
                        max_trades_per_day: int = None):
        """Set risk management parameters."""
        if risk_per_trade is not None:
            self.genome["parameters"]["risk_per_trade"] = risk_per_trade
        if max_positions is not None:
            self.genome["parameters"]["max_positions"] = max_positions
        if max_trades_per_day is not None:
            self.genome["parameters"]["max_trades_per_day"] = max_trades_per_day
        return self
    
    # ==================== EVOLUTION ====================
    
    def clone(self, new_name: str = None) -> 'StrategyGenome':
        """Create a deep copy of this genome."""
        clone = StrategyGenome(deepcopy(self.genome))
        clone.genome["id"] = str(uuid.uuid4())
        clone.genome["parent_id"] = self.id
        clone.genome["generation"] = self.genome.get("generation", 0) + 1
        clone.genome["created_at"] = datetime.now().isoformat()
        
        if new_name:
            clone.genome["name"] = new_name
        else:
            clone.genome["name"] = f"{self.name}_v{clone.genome['generation']}"
        
        return clone
    
    def mutate(self, mutation_rate: float = 0.2) -> 'StrategyGenome':
        """
        Create a mutated version of this strategy.
        
        Args:
            mutation_rate: Probability to mutate each parameter (0.0-1.0)
        
        Returns:
            New mutated genome
        """
        import random
        
        mutant = self.clone(f"{self.name}_mutant")
        
        # Mutate indicator parameters
        for indicator, params in mutant.indicators.items():
            for param_name, param_value in params.items():
                if random.random() < mutation_rate:
                    if isinstance(param_value, (int, float)):
                        # Vary by ±20%
                        delta = param_value * random.uniform(-0.2, 0.2)
                        params[param_name] = type(param_value)(param_value + delta)
        
        # Mutate exit rules
        if random.random() < mutation_rate:
            mutant.exit_rules["tp_mult"] += random.uniform(-0.3, 0.3)
            mutant.exit_rules["tp_mult"] = max(1.0, mutant.exit_rules["tp_mult"])
        
        if random.random() < mutation_rate:
            mutant.exit_rules["sl_atr"] += random.uniform(-0.2, 0.2)
            mutant.exit_rules["sl_atr"] = max(0.5, mutant.exit_rules["sl_atr"])
        
        return mutant
    
    # ==================== SERIALIZATION ====================
    
    def to_dict(self) -> Dict:
        """Export genome as dictionary."""
        return deepcopy(self.genome)
    
    def to_json(self) -> str:
        """Export genome as JSON string."""
        return json.dumps(self.genome, indent=2)
    
    def save(self, filepath: str):
        """Save genome to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.genome, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'StrategyGenome':
        """Load genome from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls(data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'StrategyGenome':
        """Create genome from JSON string."""
        data = json.loads(json_str)
        return cls(data)
    
    # ==================== DISPLAY ====================
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"Strategy: {self.name} (ID: {self.id[:8]}...)",
            f"Type: {self.type}",
            f"Symbols: {', '.join(self.symbols)}",
            f"Timeframe: {self.timeframe}",
            f"",
            f"Indicators: {len(self.indicators)}",
        ]
        for ind, params in self.indicators.items():
            lines.append(f"  - {ind}: {params}")
        
        lines.append(f"")
        lines.append(f"Entry Rules: {len(self.entry_rules)}")
        for i, rule in enumerate(self.entry_rules, 1):
            lines.append(f"  {i}. {rule['condition']} (weight: {rule['weight']})")
        
        lines.append(f"")
        lines.append(f"Exit: TP={self.exit_rules['tp_mult']}R, SL={self.exit_rules['sl_atr']}*ATR")
        
        lines.append(f"")
        lines.append(f"Risk: {self.parameters['risk_per_trade']*100}% per trade, Max {self.parameters['max_positions']} positions")
        
        return "\n".join(lines)
    
    def __repr__(self):
        return f"<StrategyGenome {self.name} ({self.type})>"
    
    def __str__(self):
        return self.summary()


# ==================== PREDEFINED TEMPLATES ====================

class StrategyTemplates:
    """Library of proven strategy templates."""
    
    @staticmethod
    def rsi_mean_reversion(symbol: str = "GOLD", timeframe: str = "M15") -> StrategyGenome:
        """Classic RSI oversold/overbought mean reversion."""
        genome = StrategyGenome()
        genome.name = f"RSI_MeanRev_{symbol}"
        genome.genome["type"] = StrategyGenome.MEAN_REVERSION
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("RSI", {"period": 14, "oversold": 30, "overbought": 70})
        genome.add_indicator("BB", {"period": 20, "std": 2.5})
        
        genome.add_entry_rule("RSI < 30", 0.5, "RSI Oversold")
        genome.add_entry_rule("close < BB_lower", 0.5, "Below Bollinger Band")
        
        genome.set_exit_rules(tp_mult=2.0, sl_atr=1.5, breakeven_trigger=1.0)
        genome.set_filter("mtf_trend", True)
        genome.set_filter("time_of_day", "London+NY")
        genome.set_risk_params(risk_per_trade=0.01, max_positions=2)
        
        return genome
    
    @staticmethod
    def ema_crossover_trend(symbol: str = "EURUSD", timeframe: str = "H1") -> StrategyGenome:
        """EMA crossover with ADX trend filter."""
        genome = StrategyGenome()
        genome.name = f"EMA_Trend_{symbol}"
        genome.genome["type"] = StrategyGenome.TREND_FOLLOWING
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("EMA_fast", {"period": 9})
        genome.add_indicator("EMA_slow", {"period": 21})
        genome.add_indicator("ADX", {"period": 14, "threshold": 25})
        
        genome.add_entry_rule("EMA_fast > EMA_slow", 0.6, "Bullish EMA Cross")
        genome.add_entry_rule("ADX > 25", 0.4, "Strong Trend")
        
        genome.set_exit_rules(tp_mult=3.0, sl_atr=2.0, trail_trigger=1.5)
        genome.set_filter("mtf_trend", True)
        genome.set_risk_params(risk_per_trade=0.015, max_positions=1)
        
        return genome
    
    @staticmethod
    def bollinger_breakout(symbol: str = "GOLD", timeframe: str = "M15") -> StrategyGenome:
        """Volatility breakout on Bollinger Band expansion."""
        genome = StrategyGenome()
        genome.name = f"BB_Breakout_{symbol}"
        genome.genome["type"] = StrategyGenome.BREAKOUT
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("BB", {"period": 20, "std": 2.0})
        genome.add_indicator("ATR", {"period": 14})
        genome.add_indicator("Volume", {"ma_period": 20})
        
        genome.add_entry_rule("close > BB_upper", 0.5, "Breakout Above Band")
        genome.add_entry_rule("volume > volume_ma * 1.3", 0.3, "Volume Surge")
        genome.add_entry_rule("ATR > ATR_ma", 0.2, "Volatility Expansion")
        
        genome.set_exit_rules(tp_mult=2.5, sl_atr=1.8, trail_trigger=1.2)
        genome.set_filter("volatility_max", 0.03)
        genome.set_risk_params(risk_per_trade=0.012, max_positions=3)
        
        return genome
    
    @staticmethod
    def macrossover_regime(symbol: str = "EURUSD", timeframe: str = "H4") -> StrategyGenome:
        """Institutional Trend-Following with HMM-style Regime Filter."""
        genome = StrategyGenome()
        genome.name = f"Regime_Trend_{symbol}"
        genome.genome["type"] = StrategyGenome.TREND_FOLLOWING
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("EMA_fast", {"period": 20})
        genome.add_indicator("EMA_slow", {"period": 50})
        genome.add_indicator("ADX", {"period": 14})
        genome.add_indicator("Regime", {"type": "VolatilityRatio", "period": 100})
        
        genome.add_entry_rule("close > EMA_fast", 0.3, "Above Fast EMA")
        genome.add_entry_rule("EMA_fast > EMA_slow", 0.4, "Bullish Alignment")
        genome.add_entry_rule("ADX > 20", 0.3, "Trend is Active")
        
        genome.set_exit_rules(tp_mult=4.0, sl_atr=2.5, trail_trigger=2.0)
        genome.set_filter("mtf_trend", True)
        genome.set_risk_params(risk_per_trade=0.01, max_positions=1)
        
        return genome

    @staticmethod
    def scalping_divergence(symbol: str = "GOLD", timeframe: str = "M5") -> StrategyGenome:
        """High-frequency mean reversion on RSI/MACD divergence."""
        genome = StrategyGenome()
        genome.name = f"Scalp_Div_{symbol}"
        genome.genome["type"] = StrategyGenome.SCALPING
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("RSI", {"period": 7})
        genome.add_indicator("MACD", {"fast": 12, "slow": 26, "signal": 9})
        
        genome.add_entry_rule("RSI < 20", 0.5, "RSI Deep Oversold")
        genome.add_entry_rule("MACD_histogram > MACD_histogram_prev", 0.5, "Momentum Shift")
        
        genome.set_exit_rules(tp_mult=1.5, sl_atr=1.0)
        genome.set_filter("time_of_day", "London+NY")
        genome.set_risk_params(risk_per_trade=0.005, max_positions=5, max_trades_per_day=30)
        
        return genome

    @staticmethod
    def liquidity_breakout(symbol: str = "GBPUSD", timeframe: str = "M15") -> StrategyGenome:
        """Breakout from consolidated zones with volume confirmation."""
        genome = StrategyGenome()
        genome.name = f"Liq_Breakout_{symbol}"
        genome.genome["type"] = StrategyGenome.BREAKOUT
        genome.set_symbols([symbol])
        genome.set_timeframe(timeframe)
        
        genome.add_indicator("BB", {"period": 50, "std": 2.0})
        genome.add_indicator("Volume", {"ma_period": 30})
        genome.add_indicator("ATR", {"period": 14})
        
        genome.add_entry_rule("close > BB_upper", 0.4, "Zone Breakout")
        genome.add_entry_rule("volume > volume_ma * 2.0", 0.4, "Liquidity Surge")
        genome.add_entry_rule("ATR > ATR_ma", 0.2, "Volatility Spike")
        
        genome.set_exit_rules(tp_mult=3.0, sl_atr=1.5, trail_trigger=1.5)
        genome.set_risk_params(risk_per_trade=0.01, max_positions=2)
        
        return genome

    @staticmethod
    def get_all_templates() -> Dict[str, StrategyGenome]:
        """Get dictionary of all available templates."""
        return {
            "RSI_MeanReversion": StrategyTemplates.rsi_mean_reversion(),
            "EMA_Trend": StrategyTemplates.ema_crossover_trend(),
            "BB_Breakout": StrategyTemplates.bollinger_breakout(),
            "Regime_Trend": StrategyTemplates.macrossover_regime(),
            "Scalp_Div": StrategyTemplates.scalping_divergence(),
            "Liq_Breakout": StrategyTemplates.liquidity_breakout()
        }


if __name__ == "__main__":
    # Demo usage
    print("=" * 60)
    print("STRATEGY GENOME - Demo")
    print("=" * 60)
    
    # Create from template
    genome = StrategyTemplates.rsi_mean_reversion("GOLD", "M15")
    print(genome)
    print()
    
    # Mutate
    mutant = genome.mutate(mutation_rate=0.3)
    print("=" * 60)
    print("MUTATED VERSION:")
    print(mutant)
    print()
    
    # Save/Load
    genome.save("test_genome.json")
    loaded = StrategyGenome.load("test_genome.json")
    print("=" * 60)
    print("LOADED FROM FILE:")
    print(loaded.name, loaded.id)
