"""
Market Context Analyzer - Provides session, volatility, and temporal context
"""

from datetime import datetime, time
import pytz
import numpy as np


class MarketContextAnalyzer:
    """Analyzes market context including sessions, volatility regime, and time factors"""
    
    # Trading session times (UTC)
    SESSIONS = {
        'TOKYO': (time(0, 0), time(9, 0)),
        'LONDON': (time(8, 0), time(16, 30)),
        'NEW_YORK': (time(13, 0), time(22, 0)),
    }
    
    def __init__(self, symbol: str, df_1h, df_4h, df_1d):
        self.symbol = symbol
        self.df_1h = df_1h
        self.df_4h = df_4h
        self.df_1d = df_1d
        
    def get_current_session(self) -> str:
        """Determine current trading session"""
        utc_now = datetime.now(pytz.UTC)
        current_time = utc_now.time()
        
        active_sessions = []
        for session, (start, end) in self.SESSIONS.items():
            if start <= current_time <= end:
                active_sessions.append(session)
        
        if not active_sessions:
            return "CLOSED / OFF-HOURS"
        elif len(active_sessions) > 1:
            return f"{' + '.join(active_sessions)} OVERLAP"
        else:
            return active_sessions[0]
    
    def analyze_volatility_regime(self) -> dict:
        """Classify current volatility regime"""
        
        # Get recent ATR values
        recent_atr = self.df_1d.tail(20)['ATR'].dropna()
        
        if len(recent_atr) == 0:
            return {'regime': 'UNKNOWN', 'description': 'Insufficient data'}
        
        current_atr = recent_atr.iloc[-1]
        avg_atr = recent_atr.mean()
        std_atr = recent_atr.std()
        
        # Classify volatility
        if current_atr > avg_atr + std_atr:
            regime = "🔥 HIGH VOLATILITY"
            description = "Above-average volatility - Wider stops recommended"
        elif current_atr < avg_atr - std_atr:
            regime = "😴 LOW VOLATILITY"
            description = "Below-average volatility - Tighter ranges, breakout potential"
        else:
            regime = "📊 NORMAL VOLATILITY"
            description = "Average volatility - Standard position sizing"
        
        return {
            'regime': regime,
            'description': description,
            'current_atr': current_atr,
            'avg_atr': avg_atr,
            'percentile': (current_atr / avg_atr - 1) * 100
        }
    
    def analyze_price_context(self) -> dict:
        """Analyze where current price sits in recent context"""
        
        # Get recent high and low (last 20 days)
        recent_high = self.df_1d.tail(20)['high'].max()
        recent_low = self.df_1d.tail(20)['low'].min()
        current_price = self.df_1d.iloc[-1]['close']
        
        # Calculate position in range
        price_range = recent_high - recent_low
        position_in_range = (current_price - recent_low) / price_range if price_range > 0 else 0.5
        
        # Classify position
        if position_in_range > 0.8:
            position = "🔝 NEAR RECENT HIGHS"
            bias = "Resistance overhead - Potential reversal zone"
        elif position_in_range < 0.2:
            position = "🔻 NEAR RECENT LOWS"
            bias = "Support below - Potential bounce zone"
        elif 0.4 <= position_in_range <= 0.6:
            position = "⚖️ MID-RANGE"
            bias = "Balanced - No directional bias from range"
        elif position_in_range > 0.6:
            position = "📈 UPPER RANGE"
            bias = "Bullish momentum - Watch for resistance"
        else:
            position ="📉 LOWER RANGE"
            bias = "Bearish pressure - Watch for support"
        
        return {
            'position': position,
            'bias': bias,
            'percentile': position_in_range * 100,
            'recent_high': recent_high,
            'recent_low': recent_low,
            'current_price': current_price
        }
    
    def generate_context_report(self) -> str:
        """Generate complete market context section"""
        
        session = self.get_current_session()
        volatility = self.analyze_volatility_regime()
        price_context = self.analyze_price_context()
        
        report = "\n## 🌍 MARKET CONTEXT\n\n"
        
        # Trading Session
        report += f"### Trading Session\n"
        report += f"**Current**: {session}\n"
        
        if "OVERLAP" in session:
            report += f"- ⚡ **High Activity Period** - Multiple sessions active\n"
            report += f"- 📈 Increased volume and volatility expected\n"
        elif "CLOSED" in session:
            report += f"- 😴 **Low Activity Period** - Outside major sessions\n"
            report += f"- ⚠️ Wider spreads and lower liquidity\n"
        
        report += "\n"
        
        # Volatility Regime
        report += f"### Volatility Analysis\n"
        report += f"**Regime**: {volatility['regime']}\n"
        report += f"- {volatility['description']}\n"
        report += f"- Current ATR: {volatility['current_atr']:.2f}\n"
        report += f"- Average ATR: {volatility['avg_atr']:.2f}\n"
        report += f"- Change: {volatility['percentile']:+.1f}% from average\n\n"
        
        # Price Context
        report += f"### Price Context (20-Day Range)\n"
        report += f"**Position**: {price_context['position']}\n"
        report += f"- {price_context['bias']}\n"
        report += f"- Range: {price_context['recent_low']:.2f} - {price_context['recent_high']:.2f}\n"
        report += f"- Current: {price_context['current_price']:.2f} ({price_context['percentile']:.0f}th percentile)\n\n"
        
        return report


class SetupScorer:
    """Scores trade setups based on multiple quality factors"""
    
    @staticmethod
    def score_setup(setup: dict, analysis: dict, confluence_zones: list) -> dict:
        """Calculate comprehensive setup quality score (0-10)"""
        
        score = 0
        factors = []
        
        entry_price = float(setup.get('entry', '0').replace(' (on breakout)', ''))
        
        # Factor 1: Risk/Reward Ratio (0-3 points)
        rr_str = setup.get('rr', '0:1')
        rr_value = float(rr_str.split(':')[0]) if ':' in rr_str else 0
        
        if rr_value >= 3.0:
            score += 3
            factors.append("Excellent R:R (3+:1)")
        elif rr_value >= 2.0:
            score += 2
            factors.append("Good R:R (2+:1)")
        elif rr_value >= 1.5:
            score += 1
            factors.append("Fair R:R (1.5+:1)")
        
        # Factor 2: Confluence (0-3 points)
        has_confluence = any(abs(c['level'] - entry_price) < 10 for c in confluence_zones)
        
        if has_confluence:
            matching_confluence = [c for c in confluence_zones if abs(c['level'] - entry_price) < 10][0]
            if matching_confluence['count'] >= 4:
                score += 3
                factors.append(f"Strong confluence ({matching_confluence['count']} TFs)")
            elif matching_confluence['count'] >= 3:
                score += 2
                factors.append(f"Moderate confluence ({matching_confluence['count']} TFs)")
        
        # Factor 3: Trend Alignment (0-2 points)
        weekly_signal = analysis.get('1W', {}).get('signal', {}).get('signal', '')
        daily_signal = analysis.get('1D', {}).get('signal', {}).get('signal', '')
        
        setup_type = setup.get('type', '')
        
        if (setup_type == 'BUY' and 'BUY' in weekly_signal) or \
           (setup_type == 'SELL' and 'SELL' in weekly_signal):
            score += 2
            factors.append("Weekly trend aligned")
        elif (setup_type == 'BUY' and 'BUY' in daily_signal) or \
             (setup_type == 'SELL' and 'SELL' in daily_signal):
            score += 1
            factors.append("Daily trend aligned")
        
        # Factor 4: Pattern Confirmation (0-2 points)
        patterns = analysis.get('1H', {}).get('patterns', [])
        bullish_patterns = [p for p in patterns if 'Bullish' in p or 'BOTTOM' in p or 'HAMMER' in p]
        bearish_patterns = [p for p in patterns if 'Bearish' in p or 'TOP' in p or 'STAR' in p]
        
        if (setup_type == 'BUY' and bullish_patterns) or \
           (setup_type == 'SELL' and bearish_patterns):
            score += 2
            factors.append(f"Pattern confirmation present")
        
        # Calculate final score (0-10 scale)
        max_possible = 10
        final_score = min(score, max_possible)
        
        # Quality rating
        if final_score >= 8:
            quality = "🏆 PREMIUM"
        elif final_score >= 6:
            quality = "✅ HIGH"
        elif final_score >= 4:
            quality = "🟡 MEDIUM"
        else:
            quality = "⚠️ LOW"
        
        return {
            'score': final_score,
            'quality': quality,
            'factors': factors,
            'max_score': max_possible
        }
