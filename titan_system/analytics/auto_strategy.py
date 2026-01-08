"""
Auto Strategy Selector
======================
Automatically selects the best strategy based on detected market regime.
Uses MarketAnalyzer's regime detection to dynamically switch strategies.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("Titan.AutoStrategy")


class StrategyType(Enum):
    """Available strategy categories."""
    MOMENTUM = "Momentum"
    TREND_FOLLOWING = "Trend Following"
    BREAKOUT = "Breakout"
    MEAN_REVERSION = "Mean Reversion"
    VOLATILITY = "Volatility"
    SCALPING = "Scalping"
    SWING = "Swing"


@dataclass
class StrategyConfig:
    """Configuration for a strategy."""
    name: str
    strategy_type: StrategyType
    preferred_regimes: List[str]
    avoid_regimes: List[str]
    min_adx: float = 0
    max_adx: float = 100
    risk_multiplier: float = 1.0
    enabled: bool = True


class AutoStrategySelector:
    """
    Automatically selects and weights strategies based on market regime.
    Provides dynamic strategy switching for optimal performance.
    """
    
    def __init__(self):
        self.strategies: Dict[str, StrategyConfig] = {}
        self.current_selections: Dict[str, str] = {}  # {symbol: strategy_name}
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register the default strategy configurations."""
        defaults = [
            StrategyConfig(
                name="EMA_Crossover",
                strategy_type=StrategyType.TREND_FOLLOWING,
                preferred_regimes=["TRENDING"],
                avoid_regimes=["HIGH_VOLATILITY", "MEAN_REVERTING"],
                min_adx=20
            ),
            StrategyConfig(
                name="RSI_Divergence",
                strategy_type=StrategyType.MEAN_REVERSION,
                preferred_regimes=["MEAN_REVERTING"],
                avoid_regimes=["TRENDING"],
                max_adx=25
            ),
            StrategyConfig(
                name="Bollinger_Band_Squeeze",
                strategy_type=StrategyType.VOLATILITY,
                preferred_regimes=["MEAN_REVERTING", "HIGH_VOLATILITY"],
                avoid_regimes=[]
            ),
            StrategyConfig(
                name="Momentum_Breakout",
                strategy_type=StrategyType.BREAKOUT,
                preferred_regimes=["TRENDING", "HIGH_VOLATILITY"],
                avoid_regimes=["MEAN_REVERTING"],
                min_adx=25
            ),
            StrategyConfig(
                name="SMC_Liquidity_Sweep",
                strategy_type=StrategyType.BREAKOUT,
                preferred_regimes=["TRENDING", "HIGH_VOLATILITY"],
                avoid_regimes=[],
                risk_multiplier=0.8  # Slightly reduced risk due to complexity
            ),
            StrategyConfig(
                name="Hidden_Divergence",
                strategy_type=StrategyType.TREND_FOLLOWING,
                preferred_regimes=["TRENDING"],
                avoid_regimes=["HIGH_VOLATILITY"],
                min_adx=20
            ),
            StrategyConfig(
                name="Scalp_EMA_RSI",
                strategy_type=StrategyType.SCALPING,
                preferred_regimes=["MEAN_REVERTING"],
                avoid_regimes=["HIGH_VOLATILITY"],
                risk_multiplier=0.5  # Reduced risk for scalping
            ),
            StrategyConfig(
                name="Swing_Trend",
                strategy_type=StrategyType.SWING,
                preferred_regimes=["TRENDING"],
                avoid_regimes=["HIGH_VOLATILITY"],
                min_adx=25,
                risk_multiplier=1.2  # Higher risk for swing trades
            )
        ]
        
        for config in defaults:
            self.register_strategy(config)
    
    def register_strategy(self, config: StrategyConfig):
        """Register a strategy configuration."""
        self.strategies[config.name] = config
        logger.debug(f"[AUTO] Registered strategy: {config.name}")
    
    def select_strategy(self, 
                        symbol: str,
                        regime: str,
                        regime_confidence: float,
                        adx: float = 25,
                        available_strategies: List[str] = None) -> Dict:
        """
        Select the best strategy for the given symbol and market conditions.
        
        Args:
            symbol: Trading symbol
            regime: Current market regime (TRENDING/MEAN_REVERTING/HIGH_VOLATILITY)
            regime_confidence: Confidence in regime detection (0-1)
            adx: Current ADX value
            available_strategies: Optional list of strategies to choose from
            
        Returns:
            Dict with selected strategy and parameters
        """
        candidates = []
        
        # Filter strategies
        for name, config in self.strategies.items():
            if not config.enabled:
                continue
            
            if available_strategies and name not in available_strategies:
                continue
            
            # Check regime compatibility
            if regime in config.avoid_regimes:
                continue
            
            # Check ADX requirements
            if adx < config.min_adx or adx > config.max_adx:
                continue
            
            # Calculate score
            score = 0
            
            # Bonus for preferred regime
            if regime in config.preferred_regimes:
                score += 50 * regime_confidence
            else:
                score += 20  # Neutral regime compatibility
            
            # ADX fitness (closer to ideal = higher score)
            ideal_adx = (config.min_adx + config.max_adx) / 2
            adx_fitness = 1 - abs(adx - ideal_adx) / 50
            score += adx_fitness * 30
            
            candidates.append({
                'name': name,
                'config': config,
                'score': score
            })
        
        if not candidates:
            # Fallback: return a conservative default
            return {
                'symbol': symbol,
                'selected_strategy': None,
                'reason': 'No compatible strategies for current regime',
                'regime': regime,
                'risk_multiplier': 0.5  # Conservative
            }
        
        # Sort by score and select best
        candidates.sort(key=lambda x: x['score'], reverse=True)
        winner = candidates[0]
        
        # Check for strategy change
        previous = self.current_selections.get(symbol)
        strategy_changed = previous != winner['name']
        
        if strategy_changed:
            self.current_selections[symbol] = winner['name']
            logger.info(f"[AUTO] {symbol}: Strategy changed from {previous} to {winner['name']} (Regime: {regime})")
        
        return {
            'symbol': symbol,
            'selected_strategy': winner['name'],
            'strategy_type': winner['config'].strategy_type.value,
            'score': round(winner['score'], 1),
            'regime': regime,
            'regime_confidence': regime_confidence,
            'risk_multiplier': winner['config'].risk_multiplier,
            'strategy_changed': strategy_changed,
            'alternatives': [c['name'] for c in candidates[1:4]]  # Top 3 alternatives
        }
    
    def select_from_analysis(self, analysis: Dict) -> Dict:
        """
        Select strategy from a MarketAnalyzer analysis result.
        
        Args:
            analysis: Output from MarketAnalyzer.analyze_symbol()
            
        Returns:
            Strategy selection with risk adjustments
        """
        if not analysis or 'regime' not in analysis:
            return {
                'symbol': analysis.get('symbol', 'UNKNOWN'),
                'selected_strategy': None,
                'reason': 'No regime data in analysis',
                'risk_multiplier': 0.5
            }
        
        regime_data = analysis['regime']
        h1_state = analysis.get('timeframes', {}).get('H1', {})
        
        selection = self.select_strategy(
            symbol=analysis['symbol'],
            regime=regime_data['current'],
            regime_confidence=regime_data['confidence'],
            adx=h1_state.get('adx', 25)
        )
        
        # Apply regime risk multiplier
        regime_risk = regime_data.get('risk_multiplier', 1.0)
        selection['risk_multiplier'] *= regime_risk
        selection['regime_risk_applied'] = regime_risk
        
        # Add warning if regime just changed
        if regime_data.get('regime_change', False):
            selection['warning'] = 'Regime just changed - reduced confidence'
            selection['risk_multiplier'] *= 0.8
        
        return selection
    
    def get_regime_strategy_matrix(self) -> Dict:
        """
        Returns a matrix showing which strategies are active for each regime.
        Useful for documentation/debugging.
        """
        regimes = ['TRENDING', 'MEAN_REVERTING', 'HIGH_VOLATILITY']
        matrix = {regime: [] for regime in regimes}
        
        for name, config in self.strategies.items():
            if not config.enabled:
                continue
            
            for regime in regimes:
                if regime in config.preferred_regimes:
                    matrix[regime].append(f"{name} [PREFERRED]")
                elif regime not in config.avoid_regimes:
                    matrix[regime].append(f"{name} [OK]")
        
        return matrix


# Convenience singleton
_default_selector = None

def get_strategy_selector() -> AutoStrategySelector:
    """Get default strategy selector instance."""
    global _default_selector
    if _default_selector is None:
        _default_selector = AutoStrategySelector()
    return _default_selector


def auto_select(analysis: Dict) -> Dict:
    """
    Quick auto-selection from MarketAnalyzer output.
    
    Usage:
        analysis = await market_analyzer.analyze_symbol("GOLD")
        selection = auto_select(analysis)
        print(selection['selected_strategy'])
    """
    return get_strategy_selector().select_from_analysis(analysis)


if __name__ == "__main__":
    # Test the selector
    print("Auto Strategy Selector Test")
    print("=" * 50)
    
    selector = AutoStrategySelector()
    
    # Show regime-strategy matrix
    print("\nRegime-Strategy Matrix:")
    matrix = selector.get_regime_strategy_matrix()
    for regime, strategies in matrix.items():
        print(f"\n{regime}:")
        for s in strategies:
            print(f"  - {s}")
    
    # Test selection
    print("\n\nTest Selections:")
    
    # Trending market
    result = selector.select_strategy("GOLD", "TRENDING", 0.75, adx=30)
    print(f"\nGOLD (Trending, ADX=30): {result['selected_strategy']}")
    print(f"  Score: {result['score']}, Risk: {result['risk_multiplier']}")
    
    # Mean reverting market
    result = selector.select_strategy("EURUSD", "MEAN_REVERTING", 0.60, adx=15)
    print(f"\nEURUSD (Mean Reverting, ADX=15): {result['selected_strategy']}")
    print(f"  Score: {result['score']}, Risk: {result['risk_multiplier']}")
    
    # High volatility market
    result = selector.select_strategy("BTCUSD", "HIGH_VOLATILITY", 0.85, adx=40)
    print(f"\nBTCUSD (High Volatility, ADX=40): {result['selected_strategy']}")
    print(f"  Score: {result['score']}, Risk: {result['risk_multiplier']}")
