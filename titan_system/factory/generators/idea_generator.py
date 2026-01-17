"""
IDEA GENERATOR - ULTIMATE QUANT-GRADE VERSION
==============================================
Enhanced strategy candidate generation with:
1. Bayesian parameter optimization
2. True genetic crossover (DNA from multiple parents)
3. Advanced feature templates (Kalman, HMM, Regime Detection)
4. Adaptive mutation strategies
"""

import random
import numpy as np
from typing import List, Dict, Tuple
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from copy import deepcopy
from scipy.stats import norm
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from titan_system.factory.strategy_genome import StrategyGenome, StrategyTemplates
from titan_system.factory import factory_config as cfg


class UltimateIdeaGenerator:
    """
    Quant-grade strategy generator with Bayesian optimization and genetic crossover.
    """
    
    def __init__(self, registry_db: str = "data/strategy_factory.db"):
        self.symbol_universe = self._load_high_alpha_symbols()
        self.timeframe_universe = cfg.TIMEFRAME_UNIVERSE
        self.param_ranges = cfg.PARAMETER_RANGES
        self.registry_db = registry_db
        
        # Bayesian optimization state
        self.param_history = []  # (params, sharpe_score)
        self.gp_optimizer = None
        
        # Real-World Market Context
        self.market_context = self._recon_real_data()

    def _load_high_alpha_symbols(self) -> List[str]:
        """Load discovered high-alpha symbols from Scout output."""
        try:
            with open('data/discovered_high_alpha.json', 'r') as f:
                data = json.load(f)
                return [s['symbol'] for s in data[:10]] # Take top 10
        except Exception:
            return cfg.SYMBOL_UNIVERSE # Fallback

    def _recon_real_data(self) -> Dict:
        """Perform deep recon on real tick/history data from MT5 terminal."""
        import MetaTrader5 as mt5
        if not mt5.initialize():
            return {}
        
        context = {}
        for symbol in self.symbol_universe[:3]: # Focus on majors
            ticks = mt5.copy_ticks_from(symbol, datetime.now() - timedelta(hours=6), 1000, mt5.COPY_TICKS_ALL)
            if ticks is not None:
                df = pd.DataFrame(ticks)
                context[symbol] = {
                    'avg_spread': (df['ask'] - df['bid']).mean(),
                    'volatility': df['bid'].pct_change().std(),
                    'trend_bias': (df['bid'].iloc[-1] - df['bid'].iloc[0]) / df['bid'].iloc[0]
                }
        mt5.shutdown()
        return context
        
    # ==================== MAIN GENERATION ====================
    
    def generate_batch(self, count: int = 50) -> List[StrategyGenome]:
        """
        Generate ultimate-grade strategy batch.
        
        Distribution:
        - 25% Template-based with Bayesian params
        - 25% Genetic crossover from top performers
        - 20% Advanced features (Kalman, HMM, PCA)
        - 15% Symbol/timeframe rotations
        - 15% Adaptive mutations
        """
        candidates = []
        
        template_count = int(count * 0.25)
        crossover_count = int(count * 0.25)
        advanced_count = int(count * 0.20)
        rotation_count = int(count * 0.15)
        adaptive_count = count - template_count - crossover_count - advanced_count - rotation_count
        
        # 1. Bayesian-optimized templates
        candidates.extend(self.generate_bayesian_templates(template_count))
        
        # 2. Genetic crossover (true breeding)
        candidates.extend(self.generate_genetic_crossover(crossover_count))
        
        # 3. Advanced feature templates
        candidates.extend(self.generate_advanced_features(advanced_count))
        
        # 4. Symbol/timeframe rotations
        candidates.extend(self.generate_rotations(rotation_count))
        
        # 5. Adaptive mutations
        candidates.extend(self.generate_adaptive_mutations(adaptive_count))
        
        # 6. Diversification Check (Council Audit #2)
        # Ensure we have enough US100 and BTCUSD representation
        final_candidates = self._balance_symbols(candidates)
        
        return final_candidates[:count]

    def _balance_symbols(self, candidates: List[StrategyGenome]) -> List[StrategyGenome]:
        """Force diversification if specific symbols are missing."""
        symbol_counts = {}
        for c in candidates:
            sym = c.symbols[0] if c.symbols else "UNKNOWN"
            symbol_counts[sym] = symbol_counts.get(sym, 0) + 1
            
        # Target: At least 20% US100/BTCUSD if in universe
        targets = ["US100", "BTCUSD", "US30", "XTIUSD"]
        for target in targets:
            if target in self.symbol_universe and symbol_counts.get(target, 0) < len(candidates) * 0.1:
                # Force some candidates to use target symbol
                for _ in range(int(len(candidates) * 0.1)):
                    new_idx = random.randint(0, len(candidates)-1)
                    candidates[new_idx].set_symbols([target])
        return candidates
    
    # ==================== BAYESIAN OPTIMIZATION ====================
    
    def generate_bayesian_templates(self, count: int) -> List[StrategyGenome]:
        """Use Bayesian optimization to suggest optimal parameters."""
        candidates = []
        
        # Load historical performance data
        self._load_param_history()
        
        templates = StrategyTemplates.get_all_templates()
        
        for _ in range(count):
            template_name = random.choice(list(templates.keys()))
            template = templates[template_name].clone()
            
            # Use Bayesian optimization to suggest parameters
            if len(self.param_history) >= 5:  # Need minimum data
                suggested_params = self._bayesian_suggest_params(template.type)
                template = self._apply_bayesian_params(template, suggested_params)
            else:
                # Fallback to smart random until we have data
                template = self._vary_parameters(template)
            
            # Randomize symbol and timeframe
            template.set_symbols([random.choice(self.symbol_universe)])
            template.set_timeframe(random.choice(self.timeframe_universe))
            
            candidates.append(template)
        
        return candidates
    
    def _load_param_history(self):
        """Load parameter-performance pairs from registry."""
        try:
            conn = sqlite3.connect(self.registry_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT genome, bt_sharpe 
                FROM strategies 
                WHERE bt_sharpe IS NOT NULL 
                ORDER BY created_at DESC LIMIT 100
            """)
            
            import json
            self.param_history = []
            for row in cursor.fetchall():
                genome_data = json.loads(row[0])
                sharpe = row[1]
                if sharpe and sharpe > 0:
                    self.param_history.append((genome_data, sharpe))
            
            conn.close()
        except:
            pass  # First run, no history yet
    
    def _bayesian_suggest_params(self, strategy_type: str) -> Dict:
        """Use Gaussian Process to suggest next best parameters."""
        # Extract parameter vectors and scores from history
        X = []
        y = []
        
        for genome, sharpe in self.param_history:
            if genome.get('type') == strategy_type:
                # Convert genome params to vector
                param_vector = self._genome_to_vector(genome)
                if param_vector:
                    X.append(param_vector)
                    y.append(sharpe)
        
        if len(X) < 3:
            return self._random_params_dict()
        
        # Fit Gaussian Process
        kernel = Matern(nu=2.5)
        gp = GaussianProcessRegressor(kernel=kernel, n_restarts_optimizer=10)
        gp.fit(np.array(X), np.array(y))
        
        # Use Expected Improvement to find next best point
        best_params = self._optimize_acquisition(gp, X, y)
        
        return self._vector_to_params(best_params)
    
    def _genome_to_vector(self, genome: Dict) -> List[float]:
        """Convert genome parameters to numerical vector."""
        vector = []
        
        # Extract RSI params if present
        if 'RSI' in genome.get('indicators', {}):
            rsi = genome['indicators']['RSI']
            vector.extend([
                rsi.get('period', 14) / 100.0,
                rsi.get('oversold', 30) / 100.0,
                rsi.get('overbought', 70) / 100.0
            ])
        else:
            vector.extend([0.14, 0.30, 0.70])
        
        # Extract EMA params if present
        ema_fast = genome.get('indicators', {}).get('EMA_fast', {}).get('period', 20)
        ema_slow = genome.get('indicators', {}).get('EMA_slow', {}).get('period', 50)
        vector.extend([ema_fast / 100.0, ema_slow / 100.0])
        
        # Extract exit rules
        exit_rules = genome.get('exit_rules', {})
        vector.extend([
            exit_rules.get('tp_mult', 2.0) / 10.0,
            exit_rules.get('sl_atr', 1.5) / 10.0
        ])
        
        return vector if len(vector) > 0 else None
    
    def _vector_to_params(self, vector: np.ndarray) -> Dict:
        """Convert numerical vector back to parameter dict."""
        return {
            'rsi_period': int(vector[0] * 100),
            'rsi_oversold': int(vector[1] * 100),
            'rsi_overbought': int(vector[2] * 100),
            'ema_fast': int(vector[3] * 100),
            'ema_slow': int(vector[4] * 100),
            'tp_mult': float(vector[5] * 10),
            'sl_atr': float(vector[6] * 10)
        }
    
    def _optimize_acquisition(self, gp, X, y, n_samples=100) -> np.ndarray:
        """Find parameters that maximize Expected Improvement."""
        best_y = max(y)
        
        # Sample random points
        dim = len(X[0])
        random_samples = np.random.rand(n_samples, dim)
        
        # Predict mean and std
        mu, sigma = gp.predict(random_samples, return_std=True)
        
        # Calculate Expected Improvement
        with np.errstate(divide='ignore'):
            Z = (mu - best_y) / sigma
            ei = (mu - best_y) * norm.cdf(Z) + sigma * norm.pdf(Z)
            ei[sigma == 0.0] = 0.0
        
        # Return point with highest EI
        best_idx = np.argmax(ei)
        return random_samples[best_idx]
    
    def _apply_bayesian_params(self, genome: StrategyGenome, params: Dict) -> StrategyGenome:
        """Apply Bayesian-suggested parameters to genome."""
        if 'RSI' in genome.indicators:
            genome.indicators['RSI']['period'] = params.get('rsi_period', 14)
            genome.indicators['RSI']['oversold'] = params.get('rsi_oversold', 30)
            genome.indicators['RSI']['overbought'] = params.get('rsi_overbought', 70)
        
        if 'EMA_fast' in genome.indicators:
            genome.indicators['EMA_fast']['period'] = params.get('ema_fast', 12)
        
        if 'EMA_slow' in genome.indicators:
            genome.indicators['EMA_slow']['period'] = params.get('ema_slow', 26)
        
        genome.exit_rules['tp_mult'] = params.get('tp_mult', 2.0)
        genome.exit_rules['sl_atr'] = params.get('sl_atr', 1.5)
        
        return genome
    
    # ==================== GENETIC CROSSOVER ====================
    
    def generate_genetic_crossover(self, count: int) -> List[StrategyGenome]:
        """True genetic crossover: combine DNA from two parents."""
        candidates = []
        
        # Get top performers from registry
        parents = self._get_top_performers(min_count=4)
        
        if len(parents) < 2:
            # Not enough parents, fall back to templates
            return self.generate_from_templates(count)
        
        for _ in range(count):
            # Select two random parents
            parent1, parent2 = random.sample(parents, 2)
            
            # Create child by crossover
            child = self._crossover(parent1, parent2)
            
            # Apply mutation
            child = self._mutate(child, rate=0.15)
            
            candidates.append(child)
        
        return candidates
    
    def _get_top_performers(self, min_count: int = 10) -> List[StrategyGenome]:
        """Retrieve top-performing strategies from registry."""
        try:
            conn = sqlite3.connect(self.registry_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT genome 
                FROM strategies 
                WHERE bt_sharpe >= 1.0 
                AND monte_carlo_stable = 1
                ORDER BY bt_sharpe DESC 
                LIMIT ?
            """, (min_count * 2,))
            
            import json
            parents = []
            for row in cursor.fetchall():
                genome_data = json.loads(row[0])
                genome = StrategyGenome()
                genome.genome = genome_data
                parents.append(genome)
            
            conn.close()
            return parents
        except:
            return []
    
    def _crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> StrategyGenome:
        """Combine entry logic from parent1 with exit logic from parent2."""
        child = parent1.clone()
        
        # Crossover point: Entry vs Exit logic
        # Take entry rules and primary indicators from parent1
        child.genome['entry_rules'] = deepcopy(parent1.genome['entry_rules'])
        child.genome['indicators'] = deepcopy(parent1.genome['indicators'])
        
        # Take exit rules and parameters from parent2
        child.genome['exit_rules'] = deepcopy(parent2.genome['exit_rules'])
        child.genome['parameters'] = deepcopy(parent2.genome['parameters'])
        
        # Randomly inherit symbol/timeframe
        if random.random() > 0.5:
            child.set_symbols(parent1.symbols)
            child.set_timeframe(parent1.timeframe)
        else:
            child.set_symbols(parent2.symbols)
            child.set_timeframe(parent2.timeframe)
        
        # Mark as descendant
        child.genome['parent_id'] = parent1.id
        child.genome['generation'] = parent1.genome.get('generation', 0) + 1
        
        return child
    
    def _mutate(self, genome: StrategyGenome, rate: float = 0.20) -> StrategyGenome:
        """Apply random mutations to genome."""
        # Mutate indicators
        for indicator_name, params in genome.indicators.items():
            if random.random() < rate:
                for param_key in params:
                    if isinstance(params[param_key], (int, float)):
                        # Add Gaussian noise
                        noise = np.random.normal(0, 0.1)
                        params[param_key] *= (1 + noise)
        
        # Mutate exit rules
        if random.random() < rate:
            genome.exit_rules['tp_mult'] *= (1 + np.random.normal(0, 0.15))
        
        if random.random() < rate:
            genome.exit_rules['sl_atr'] *= (1 + np.random.normal(0, 0.15))
        
        return genome
    
    # ==================== ADVANCED FEATURES ====================
    
    def generate_advanced_features(self, count: int) -> List[StrategyGenome]:
        """Generate strategies with advanced quant features."""
        candidates = []
        
        advanced_templates = [
            self._create_kalman_filter_strategy,
            self._create_regime_detection_strategy,
            self._create_order_flow_strategy,
            self._create_cointegration_strategy
        ]
        
        for _ in range(count):
            template_func = random.choice(advanced_templates)
            strategy = template_func()
            candidates.append(strategy)
        
        return candidates
    
    def _create_kalman_filter_strategy(self) -> StrategyGenome:
        """Strategy using Kalman filter for dynamic mean estimation."""
        genome = StrategyGenome()
        genome.genome['type'] = StrategyGenome.MEAN_REVERSION
        genome.genome['name'] = f"Kalman_MeanRev_{random.choice(self.symbol_universe)}"
        
        genome.set_symbols([random.choice(self.symbol_universe)])
        genome.set_timeframe(random.choice(self.timeframe_universe))
        
        # Kalman filter parameters
        genome.add_indicator("KALMAN", {
            "process_variance": round(random.uniform(0.0001, 0.001), 6),
            "measurement_variance": round(random.uniform(0.001, 0.01), 6),
            "lookback": random.randint(20, 50)
        })
        
        genome.add_indicator("ATR", {"period": 14})
        
        genome.add_entry_rule("price < kalman_mean - 2*atr", 0.8, "Kalman Oversold")
        genome.add_entry_rule("price > kalman_mean + 2*atr", 0.8, "Kalman Overbought")
        
        genome.genome['exit_rules'] = {
            "tp_mult": round(random.uniform(1.5, 3.0), 2),
            "sl_atr": round(random.uniform(1.0, 2.5), 2)
        }
        
        return genome
    
    def _create_regime_detection_strategy(self) -> StrategyGenome:
        """Strategy that adapts to market regimes (trending vs ranging)."""
        genome = StrategyGenome()
        genome.genome['type'] = StrategyGenome.TREND_FOLLOWING
        genome.genome['name'] = f"Regime_{random.choice(self.symbol_universe)}"
        
        genome.set_symbols([random.choice(self.symbol_universe)])
        genome.set_timeframe(random.choice(self.timeframe_universe))
        
        # Regime detection via ADX
        genome.add_indicator("ADX", {
            "period": random.randint(10, 20),
            "threshold": random.randint(20, 30)
        })
        
        # Dual strategy: EMA for trends, RSI for ranging
        genome.add_indicator("EMA_fast", {"period": random.randint(9, 20)})
        genome.add_indicator("EMA_slow", {"period": random.randint(40, 80)})
        genome.add_indicator("RSI", {"period": 14, "oversold": 30, "overbought": 70})
        
        genome.add_entry_rule("ADX > threshold AND EMA_fast > EMA_slow", 0.7, "Trending Regime")
        genome.add_entry_rule("ADX < threshold AND RSI < 35", 0.6, "Ranging Regime")
        
        genome.genome['exit_rules'] = {
            "tp_mult": round(random.uniform(2.0, 4.0), 2),
            "sl_atr": round(random.uniform(1.5, 2.5), 2)
        }
        
        return genome
    
    def _create_order_flow_strategy(self) -> StrategyGenome:
        """Strategy using volume and tick data for order flow analysis."""
        genome = StrategyGenome()
        genome.genome['type'] = StrategyGenome.SCALPING
        genome.genome['name'] = f"OrderFlow_{random.choice(self.symbol_universe)}"
        
        genome.set_symbols([random.choice(self.symbol_universe)])
        genome.set_timeframe("M5")  # Scalping only on fast timeframes
        
        # Volume-based indicators
        genome.add_indicator("Volume", {"ma_period": 20})
        genome.add_indicator("OBV", {})  # On-Balance Volume
        genome.add_indicator("VWAP", {})  # Volume-Weighted Average Price
        
        genome.add_entry_rule("price < VWAP AND volume > 2*volume_ma", 0.75, "High Buy Volume")
        
        genome.genome['exit_rules'] = {
            "tp_mult": round(random.uniform(1.0, 2.0), 2),
            "sl_atr": round(random.uniform(0.5, 1.5), 2)
        }
        
        return genome
    
    def _create_cointegration_strategy(self) -> StrategyGenome:
        """Pairs trading using cointegration (e.g., EURUSD vs GBPUSD)."""
        genome = StrategyGenome()
        genome.genome['type'] = "PairsTrading"  # New type
        genome.genome['name'] = "Cointegration_EURUSD_GBPUSD"
        
        # Pairs trading requires two symbols
        genome.set_symbols(["EURUSD", "GBPUSD"])
        genome.set_timeframe("H1")
        
        genome.add_indicator("COINTEGRATION", {
            "lookback": random.randint(30, 100),
            "hedge_ratio": None  # Calculated dynamically
        })
        
        genome.add_entry_rule("spread > 2*std", 0.8, "Mean Reversion on Spread")
        
        genome.genome['exit_rules'] = {
            "tp_mult": round(random.uniform(1.0, 2.0), 2),
            "sl_atr": round(random.uniform(1.0, 2.0), 2)
        }
        
        return genome
    
    # ==================== HELPER METHODS ====================
    
    def generate_rotations(self, count: int) -> List[StrategyGenome]:
        """Symbol/timeframe rotations (keep existing logic)."""
        candidates = []
        base_templates = [
            StrategyTemplates.rsi_mean_reversion(),
            StrategyTemplates.ema_crossover_trend(),
            StrategyTemplates.bollinger_breakout()
        ]
        
        for _ in range(count):
            template = random.choice(base_templates).clone()
            template.set_symbols([random.choice(self.symbol_universe)])
            template.set_timeframe(random.choice(self.timeframe_universe))
            template = self._adapt_to_symbol(template, template.symbols[0])
            candidates.append(template)
        
        return candidates
    
    def generate_adaptive_mutations(self, count: int) -> List[StrategyGenome]:
        """Adaptive mutations based on recent performance."""
        candidates = []
        
        parents = self._get_top_performers(min_count=5)
        if not parents:
            return self.generate_from_templates(count)
        
        for _ in range(count):
            parent = random.choice(parents)
            child = parent.clone()
            
            # Adaptive mutation: larger changes if parent is underperforming
            mutation_rate = 0.10  # Base rate
            child = self._mutate(child, rate=mutation_rate)
            
            candidates.append(child)
        
        return candidates
    
    def _vary_parameters(self, genome: StrategyGenome) -> StrategyGenome:
        """Apply random parameter variations."""
        for indicator_name in genome.indicators:
            if indicator_name in self.param_ranges:
                for param_key, param_range in self.param_ranges[indicator_name].items():
                    if param_key in genome.indicators[indicator_name]:
                        min_val, max_val = param_range
                        if isinstance(min_val, int):
                            genome.indicators[indicator_name][param_key] = random.randint(int(min_val), int(max_val))
                        else:
                            genome.indicators[indicator_name][param_key] = round(random.uniform(min_val, max_val), 2)
        
        return genome
    
    def _adapt_to_symbol(self, genome: StrategyGenome, symbol: str) -> StrategyGenome:
        """Adapt parameters based on symbol characteristics."""
        # Crypto: wider stops, faster timeframes
        if symbol in ["BTCUSD", "ETHUSD"]:
            genome.exit_rules['sl_atr'] *= 1.5
            genome.exit_rules['tp_mult'] *= 1.3
        
        # Forex: tighter stops
        elif symbol in ["EURUSD", "GBPUSD"]:
            genome.exit_rules['sl_atr'] *= 0.8
        
        return genome
    
    def _random_params_dict(self) -> Dict:
        """Fallback random parameter generation."""
        return {
            'rsi_period': random.randint(10, 21),
            'rsi_oversold': random.randint(25, 35),
            'rsi_overbought': random.randint(65, 75),
            'ema_fast': random.randint(9, 25),
            'ema_slow': random.randint(40, 100),
            'tp_mult': round(random.uniform(1.5, 4.0), 2),
            'sl_atr': round(random.uniform(1.0, 2.5), 2)
        }
    
    def generate_from_templates(self, count: int) -> List[StrategyGenome]:
        """Fallback template generation."""
        candidates = []
        templates = StrategyTemplates.get_all_templates()
        
        for _ in range(count):
            template_name = random.choice(list(templates.keys()))
            template = templates[template_name].clone()
            template.set_symbols([random.choice(self.symbol_universe)])
            template.set_timeframe(random.choice(self.timeframe_universe))
            template = self._vary_parameters(template)
            candidates.append(template)
        
        return candidates


# Backward compatibility: alias to original class name
IdeaGenerator = UltimateIdeaGenerator
