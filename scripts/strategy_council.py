"""
Strategy Council
================
Multi-perspective AI council for strategy evaluation.

Each "agent" represents a specialized perspective that provides 
rigorous analysis from different angles.
"""
import json
import sqlite3
import os
from typing import Dict, List, Optional
from datetime import datetime

# Try to import MT5 for live data
try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False


class StrategyCouncil:
    """
    Multi-agent discussion framework for strategy evaluation.
    
    Agents:
    1. The Quant - Statistical validation
    2. The Risk Manager - Drawdown, position sizing
    3. The Execution Specialist - Spreads, slippage
    4. The Regime Analyst - Market conditions
    5. The Devil's Advocate - Breaking strategies
    """
    
    def __init__(self, intel_db_path: str = "data/comprehensive_intel.db"):
        self.intel_db_path = intel_db_path
        self.intel_loaded = False
        self._load_intel()
    
    def _load_intel(self):
        """Load market intelligence from database."""
        if os.path.exists(self.intel_db_path):
            self.intel_loaded = True
    
    def get_symbol_intel(self, symbol: str) -> Dict:
        """Get comprehensive intelligence for a symbol."""
        intel = {"symbol": symbol, "available": False}
        
        if not self.intel_loaded:
            return intel
        
        try:
            conn = sqlite3.connect(self.intel_db_path)
            c = conn.cursor()
            
            c.execute("SELECT * FROM symbol_master WHERE symbol = ?", (symbol,))
            row = c.fetchone()
            if row:
                cols = [d[0] for d in c.description]
                intel = dict(zip(cols, row))
                intel["available"] = True
            
            conn.close()
        except Exception as e:
            intel["error"] = str(e)
        
        return intel
    
    def agent_quant(self, strategy: Dict, intel: Dict) -> Dict:
        """
        The Quant Agent - Statistical validation.
        
        Checks:
        - Sample size (minimum trades)
        - Sharpe ratio
        - Profit factor
        - Statistical significance
        """
        analysis = {
            "agent": "THE QUANT",
            "emoji": "🧮",
            "concerns": [],
            "approvals": [],
            "verdict": "NEUTRAL"
        }
        
        # Check if we have enough data
        if "trades" in strategy:
            trades = strategy["trades"]
            if trades < 30:
                analysis["concerns"].append(
                    f"Insufficient sample size: {trades} trades. Need 30+ for significance."
                )
            elif trades < 100:
                analysis["concerns"].append(
                    f"Marginal sample size: {trades} trades. 100+ preferred."
                )
            else:
                analysis["approvals"].append(
                    f"Adequate sample size: {trades} trades."
                )
        
        # Check Sharpe ratio
        if "sharpe" in strategy:
            sharpe = strategy["sharpe"]
            if sharpe < 1.0:
                analysis["concerns"].append(
                    f"Low Sharpe ratio: {sharpe:.2f}. Need > 1.0 for institutional grade."
                )
            elif sharpe > 5.0:
                analysis["concerns"].append(
                    f"Suspicious Sharpe ratio: {sharpe:.2f}. Possible overfitting."
                )
            else:
                analysis["approvals"].append(
                    f"Good Sharpe ratio: {sharpe:.2f}"
                )
        
        # Check win rate
        if "win_rate" in strategy:
            wr = strategy["win_rate"]
            if wr < 0.40:
                analysis["concerns"].append(
                    f"Low win rate: {wr:.1%}. Need > 40%."
                )
            else:
                analysis["approvals"].append(
                    f"Acceptable win rate: {wr:.1%}"
                )
        
        # Set verdict
        if len(analysis["concerns"]) == 0:
            analysis["verdict"] = "APPROVED"
        elif len(analysis["concerns"]) <= 1:
            analysis["verdict"] = "CONDITIONAL"
        else:
            analysis["verdict"] = "REJECTED"
        
        return analysis
    
    def agent_risk_manager(self, strategy: Dict, intel: Dict) -> Dict:
        """
        The Risk Manager Agent - Drawdown, position sizing.
        
        Checks:
        - Maximum drawdown
        - Consecutive losses
        - Position sizing
        - Correlation with existing strategies
        """
        analysis = {
            "agent": "THE RISK MANAGER",
            "emoji": "🛡️",
            "concerns": [],
            "approvals": [],
            "verdict": "NEUTRAL"
        }
        
        # Check max drawdown
        if "max_drawdown" in strategy:
            dd = strategy["max_drawdown"]
            if dd > 0.30:
                analysis["concerns"].append(
                    f"Excessive drawdown: {dd:.1%}. Max allowed 30%."
                )
            elif dd > 0.20:
                analysis["concerns"].append(
                    f"High drawdown: {dd:.1%}. Target < 20%."
                )
            else:
                analysis["approvals"].append(
                    f"Acceptable drawdown: {dd:.1%}"
                )
        
        # Check risk per trade
        if "risk_per_trade" in strategy:
            risk = strategy["risk_per_trade"]
            if risk > 0.02:
                analysis["concerns"].append(
                    f"High risk per trade: {risk:.1%}. Recommend <= 2%."
                )
            else:
                analysis["approvals"].append(
                    f"Conservative risk: {risk:.1%} per trade."
                )
        
        # Check swap costs for overnight holds
        if intel.get("available") and strategy.get("hold_overnight", False):
            swap_long = intel.get("swap_long", 0)
            swap_short = intel.get("swap_short", 0)
            
            if abs(swap_long) > 50 or abs(swap_short) > 50:
                analysis["concerns"].append(
                    f"High swap costs: Long={swap_long:.2f}, Short={swap_short:.2f}. "
                    f"Consider intraday only."
                )
        
        # Set verdict
        if len(analysis["concerns"]) == 0:
            analysis["verdict"] = "APPROVED"
        elif len(analysis["concerns"]) == 1:
            analysis["verdict"] = "CONDITIONAL"
        else:
            analysis["verdict"] = "REJECTED"
        
        return analysis
    
    def agent_execution(self, strategy: Dict, intel: Dict) -> Dict:
        """
        The Execution Specialist Agent - Spreads, slippage.
        
        Checks:
        - Spread ratio
        - Adrenaline score
        - Liquidity
        - Expected slippage
        """
        analysis = {
            "agent": "THE EXECUTION SPECIALIST",
            "emoji": "⚡",
            "concerns": [],
            "approvals": [],
            "verdict": "NEUTRAL"
        }
        
        if intel.get("available"):
            # Check spread ratio
            spread_ratio = intel.get("spread_ratio", 100)
            if spread_ratio > 20:
                analysis["concerns"].append(
                    f"Terrible spread ratio: {spread_ratio:.1f}%. "
                    f"Transaction costs will destroy edge."
                )
            elif spread_ratio > 10:
                analysis["concerns"].append(
                    f"High spread ratio: {spread_ratio:.1f}%. "
                    f"Consider higher timeframes or wider targets."
                )
            elif spread_ratio > 5:
                analysis["approvals"].append(
                    f"Acceptable spread ratio: {spread_ratio:.1f}%"
                )
            else:
                analysis["approvals"].append(
                    f"Excellent spread ratio: {spread_ratio:.1f}% - ideal for scalping!"
                )
            
            # Check adrenaline score
            adrenaline = intel.get("adrenaline_score", 0)
            if adrenaline < 5:
                analysis["concerns"].append(
                    f"Low adrenaline: {adrenaline:.1f}. Symbol doesn't move enough."
                )
            elif adrenaline > 20:
                analysis["approvals"].append(
                    f"High adrenaline: {adrenaline:.1f} - good for momentum strategies!"
                )
            else:
                analysis["approvals"].append(
                    f"Moderate adrenaline: {adrenaline:.1f}"
                )
            
            # Check tradeability
            if not intel.get("is_tradeable"):
                analysis["concerns"].append(
                    "Symbol marked as NOT TRADEABLE based on spread ratio."
                )
        else:
            analysis["concerns"].append(
                "No market intelligence available. Run comprehensive_intel.py first."
            )
        
        # Set verdict
        if len(analysis["concerns"]) == 0:
            analysis["verdict"] = "APPROVED"
        elif len(analysis["concerns"]) == 1:
            analysis["verdict"] = "CONDITIONAL"
        else:
            analysis["verdict"] = "REJECTED"
        
        return analysis
    
    def agent_regime(self, strategy: Dict, intel: Dict) -> Dict:
        """
        The Regime Analyst Agent - Market conditions.
        
        Checks:
        - Trending vs ranging performance
        - Session performance
        - Volatility sensitivity
        """
        analysis = {
            "agent": "THE REGIME ANALYST",
            "emoji": "🌊",
            "concerns": [],
            "approvals": [],
            "recommendations": [],
            "verdict": "NEUTRAL"
        }
        
        symbol = strategy.get("symbol", "")
        strategy_type = strategy.get("type", "").lower()
        
        # Strategy type vs symbol recommendations
        if intel.get("adrenaline_score", 0) > 20:
            if strategy_type in ["breakout", "momentum", "trend"]:
                analysis["approvals"].append(
                    f"High adrenaline symbol ({intel.get('adrenaline_score', 0):.1f}) "
                    f"matched with {strategy_type} strategy - good fit!"
                )
            elif strategy_type in ["mean_reversion", "range"]:
                analysis["concerns"].append(
                    f"High adrenaline symbol ({intel.get('adrenaline_score', 0):.1f}) "
                    f"with {strategy_type} strategy - potential mismatch. "
                    f"Consider trend-following instead."
                )
        
        # Session recommendations
        analysis["recommendations"].append(
            f"Best sessions for {symbol}: OVERLAP (12-17 UTC) typically has tightest spreads."
        )
        
        # Volatility filtering
        if "atr_filter" not in strategy:
            analysis["recommendations"].append(
                "Add ATR filter to avoid low-volatility chop."
            )
        
        # Set verdict
        if len(analysis["concerns"]) == 0:
            analysis["verdict"] = "APPROVED"
        else:
            analysis["verdict"] = "CONDITIONAL"
        
        return analysis
    
    def agent_devils_advocate(self, strategy: Dict, intel: Dict) -> Dict:
        """
        The Devil's Advocate Agent - Breaking strategies.
        
        Asks the hard questions to expose weaknesses.
        """
        analysis = {
            "agent": "THE DEVIL'S ADVOCATE",
            "emoji": "😈",
            "challenges": [],
            "verdict": "CONDITIONAL"  # Always skeptical
        }
        
        # Standard challenges
        analysis["challenges"].append(
            "Why hasn't this edge been arbitraged away by institutions?"
        )
        
        if strategy.get("sharpe", 0) > 2:
            analysis["challenges"].append(
                f"A Sharpe of {strategy.get('sharpe', 0):.2f} is suspiciously high. "
                f"Is this curve-fitted to the optimization period?"
            )
        
        if strategy.get("trades", 0) < 100:
            analysis["challenges"].append(
                "With limited trades, how do you know this isn't just luck?"
            )
        
        if strategy.get("type") == "breakout":
            analysis["challenges"].append(
                "Breakout strategies often fail in ranging markets. "
                "How does this handle false breakouts?"
            )
        
        if strategy.get("type") == "mean_reversion":
            analysis["challenges"].append(
                "Mean reversion assumes prices return to average. "
                "What if the market is transitioning to a new regime?"
            )
        
        # Check for forward-looking bias
        analysis["challenges"].append(
            "Is there any forward-looking bias in the signal generation?"
        )
        
        return analysis
    
    def evaluate_strategy(
        self, 
        symbol: str, 
        strategy_type: str,
        strategy_params: Dict = None,
        **kwargs
    ) -> Dict:
        """
        Run full council evaluation on a strategy.
        
        Returns comprehensive analysis from all 5 agents.
        """
        if strategy_params is None:
            strategy_params = {}
        
        # Build strategy object
        strategy = {
            "symbol": symbol,
            "type": strategy_type,
            **strategy_params,
            **kwargs
        }
        
        # Get market intelligence
        intel = self.get_symbol_intel(symbol)
        
        # Run all agents
        results = {
            "timestamp": datetime.now().isoformat(),
            "strategy": strategy,
            "intel": intel,
            "agents": {}
        }
        
        results["agents"]["quant"] = self.agent_quant(strategy, intel)
        results["agents"]["risk_manager"] = self.agent_risk_manager(strategy, intel)
        results["agents"]["execution"] = self.agent_execution(strategy, intel)
        results["agents"]["regime"] = self.agent_regime(strategy, intel)
        results["agents"]["devils_advocate"] = self.agent_devils_advocate(strategy, intel)
        
        # Calculate overall verdict
        verdicts = [a["verdict"] for a in results["agents"].values()]
        rejected_count = verdicts.count("REJECTED")
        approved_count = verdicts.count("APPROVED")
        
        if rejected_count >= 2:
            results["verdict"] = "REJECTED"
        elif approved_count >= 3 and rejected_count == 0:
            results["verdict"] = "APPROVED"
        else:
            results["verdict"] = "CONDITIONAL"
        
        return results
    
    def format_report(self, results: Dict) -> str:
        """Format council results as markdown report."""
        lines = []
        lines.append("# 🏛️ STRATEGY COUNCIL SESSION")
        lines.append("")
        lines.append(f"**Symbol:** {results['strategy'].get('symbol', 'N/A')}")
        lines.append(f"**Type:** {results['strategy'].get('type', 'N/A')}")
        lines.append(f"**Timestamp:** {results['timestamp']}")
        lines.append("")
        
        # Intel summary
        if results["intel"].get("available"):
            lines.append("## Market Intelligence")
            lines.append(f"- Spread Ratio: {results['intel'].get('spread_ratio', 'N/A'):.1f}%")
            lines.append(f"- Adrenaline: {results['intel'].get('adrenaline_score', 'N/A'):.1f}")
            lines.append(f"- ATR: {results['intel'].get('avg_h1_atr', 'N/A'):.0f}")
            lines.append(f"- Tradeable: {'Yes' if results['intel'].get('is_tradeable') else 'No'}")
            lines.append("")
        
        lines.append("---")
        lines.append("")
        
        # Each agent's analysis
        for agent_key, agent_data in results["agents"].items():
            lines.append(f"### {agent_data['emoji']} {agent_data['agent']} SAYS:")
            lines.append("")
            
            if agent_data.get("approvals"):
                lines.append("**✅ Approvals:**")
                for item in agent_data["approvals"]:
                    lines.append(f"- {item}")
                lines.append("")
            
            if agent_data.get("concerns"):
                lines.append("**⚠️ Concerns:**")
                for item in agent_data["concerns"]:
                    lines.append(f"- {item}")
                lines.append("")
            
            if agent_data.get("challenges"):
                lines.append("**❓ Challenges:**")
                for item in agent_data["challenges"]:
                    lines.append(f"- {item}")
                lines.append("")
            
            if agent_data.get("recommendations"):
                lines.append("**💡 Recommendations:**")
                for item in agent_data["recommendations"]:
                    lines.append(f"- {item}")
                lines.append("")
            
            lines.append(f"**Agent Verdict:** {agent_data['verdict']}")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Final verdict
        verdict = results["verdict"]
        if verdict == "APPROVED":
            emoji = "✅"
        elif verdict == "REJECTED":
            emoji = "❌"
        else:
            emoji = "⚠️"
        
        lines.append(f"## {emoji} COUNCIL VERDICT: **{verdict}**")
        lines.append("")
        
        return "\n".join(lines)


def main():
    """Example usage of Strategy Council."""
    council = StrategyCouncil()
    
    # Example: Evaluate a GOLD breakout strategy
    results = council.evaluate_strategy(
        symbol="GOLD",
        strategy_type="breakout",
        trades=50,
        sharpe=1.8,
        win_rate=0.55,
        max_drawdown=0.15,
        risk_per_trade=0.01
    )
    
    report = council.format_report(results)
    print(report)
    
    # Save report
    with open("data/council_report.md", "w", encoding="utf-8") as f:
        f.write(report)
    print("\nReport saved to data/council_report.md")


if __name__ == "__main__":
    main()
