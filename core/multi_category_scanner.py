"""
Multi-Category Signal Scanner
Scans across Forex, Metals, Indices, Crypto for trading opportunities
"""
import MetaTrader5 as mt5
try:
    from core.mt5_interface import MT5Interface
    from core.strategy import Strategy
except ImportError:
    from mt5_interface import MT5Interface
    from strategy import Strategy
import pandas as pd
import numpy as np
from datetime import datetime

class MultiCategoryScanner:
    def __init__(self):
        self.interface = MT5Interface()
        self.categories = {
            "Major Forex": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD"],
            "Cross Pairs": ["EURJPY", "GBPJPY", "EURGBP", "AUDNZD", "EURAUD", "CADJPY"],
            "Metals": ["XAUUSD", "XAGUSD", "XPTUSD", "XPDUSD"],
            "Indices": ["US30", "US500", "NAS100", "UK100", "GER40", "FRA40"],
            "Crypto": ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD"]
        }
        
    def scan_all_categories(self):
        """Scan all categories and return detailed signals"""
        if not self.interface.start():
            print("Failed to connect to MT5")
            return {}
            
        results = {}
        
        for category, symbols in self.categories.items():
            print(f"\n🔍 Scanning {category}...")
            category_signals = []
            
            for symbol in symbols:
                try:
                    # Check if symbol exists
                    symbol_info = mt5.symbol_info(symbol)
                    if not symbol_info:
                        continue
                        
                    # Enable symbol
                    if not symbol_info.visible:
                        if not mt5.symbol_select(symbol, True):
                            continue
                    
                    # Get data
                    df = self.interface.get_closes(symbol, mt5.TIMEFRAME_H1, 200)
                    if df is None or len(df) < 100:
                        continue
                    
                    # Analyze
                    strat = Strategy(symbol, mt5.TIMEFRAME_H1)
                    signal = strat.generate_signal(df)
                    
                    # Calculate metrics
                    current_price = df['close'].iloc[-1]
                    prev_close = df['close'].iloc[-2]
                    change_24h = ((current_price - prev_close) / prev_close) * 100
                    
                    # ATR for SL/TP
                    df['tr'] = np.maximum(
                        df['high'] - df['low'],
                        np.abs(df['high'] - df['close'].shift(1))
                    )
                    atr = df['tr'].rolling(14).mean().iloc[-1]
                    
                    # Trend
                    sma_short = df['SMA_30'].iloc[-1] if 'SMA_30' in df else current_price
                    sma_long = df['SMA_100'].iloc[-1] if 'SMA_100' in df else current_price
                    trend = "BULLISH 📈" if sma_short > sma_long else "BEARISH 📉"
                    
                    # SL/TP
                    if signal == 'BUY':
                        sl = current_price - (atr * 1.5)
                        tp = current_price + (atr * 3.0)
                        rr_ratio = 2.0
                    elif signal == 'SELL':
                        sl = current_price + (atr * 1.5)
                        tp = current_price - (atr * 3.0)
                        rr_ratio = 2.0
                    else:
                        sl = 0
                        tp = 0
                        rr_ratio = 0
                    
                    # Risk level
                    vol_ratio = (atr / current_price) * 100
                    risk_level = "HIGH ⚡" if vol_ratio > 0.1 else "MODERATE 📊" if vol_ratio > 0.05 else "LOW 🛡️"
                    
                    signal_data = {
                        "symbol": symbol,
                        "signal": signal,
                        "price": current_price,
                        "trend": trend,
                        "change_24h": change_24h,
                        "sl": sl,
                        "tp": tp,
                        "rr_ratio": rr_ratio,
                        "atr": atr,
                        "volatility": vol_ratio,
                        "risk": risk_level,
                        "spread": symbol_info.spread
                    }
                    
                    category_signals.append(signal_data)
                    
                except Exception as e:
                    print(f"  ⚠️ Error scanning {symbol}: {e}")
                    continue
            
            results[category] = category_signals
            print(f"  ✅ Found {len(category_signals)} active symbols")
        
        self.interface.shutdown()
        return results

def generate_html_report(scan_results):
    """Generate detailed HTML email report"""
    
    html = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
           background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
           margin: 0; padding: 20px; }}
    .container {{ max-width: 900px; margin: 0 auto; background: white; 
                  border-radius: 16px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
    .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); 
               color: white; padding: 40px; border-radius: 16px 16px 0 0; }}
    .header h1 {{ margin: 0; font-size: 32px; font-weight: 900; letter-spacing: -1px; }}
    .header p {{ margin: 15px 0 0; opacity: 0.9; font-size: 16px; }}
    
    .category {{ margin: 30px; }}
    .category-title {{ font-size: 20px; font-weight: 700; color: #1e293b; 
                       margin-bottom: 20px; padding-bottom: 10px; 
                       border-bottom: 3px solid #e2e8f0; }}
    
    .signal-card {{ background: linear-gradient(135deg, #f8fafc 0%, #ffffff 100%); 
                    border: 2px solid #e2e8f0; border-radius: 12px; 
                    padding: 20px; margin-bottom: 20px; 
                    transition: transform 0.2s; }}
    .signal-card:hover {{ transform: translateY(-2px); box-shadow: 0 8px 16px rgba(0,0,0,0.1); }}
    
    .signal-header {{ display: flex; justify-content: space-between; align-items: center; 
                      margin-bottom: 15px; }}
    .symbol-name {{ font-size: 24px; font-weight: 800; color: #0f172a; }}
    
    .action-badge {{ padding: 10px 20px; border-radius: 8px; font-weight: 800; 
                     font-size: 14px; letter-spacing: 1px; }}
    .buy-badge {{ background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                  color: white; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4); }}
    .sell-badge {{ background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); 
                   color: white; box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4); }}
    .hold-badge {{ background: #94a3b8; color: white; }}
    
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 15px; margin-top: 15px; }}
    .metric {{ background: #f1f5f9; padding: 12px; border-radius: 8px; }}
    .metric-label {{ font-size: 11px; color: #64748b; font-weight: 600; 
                     text-transform: uppercase; letter-spacing: 0.5px; }}
    .metric-value {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 5px; }}
    
    .trade-plan {{ background: #eff6ff; border-left: 4px solid #3b82f6; 
                   padding: 15px; margin-top: 15px; border-radius: 4px; }}
    .trade-plan-title {{ font-weight: 700; color: #1e40af; margin-bottom: 8px; }}
    
    .no-signals {{ text-align: center; padding: 40px; color: #64748b; }}
    
    .footer {{ background: #f8fafc; padding: 30px; text-align: center; 
               color: #64748b; font-size: 13px; border-radius: 0 0 16px 16px; }}
</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Multi-Category Signal Report</h1>
            <p>Comprehensive Analysis Across 5 Asset Classes</p>
            <p>Generated: {datetime.now().strftime('%B %d, %Y at %H:%M IST')}</p>
        </div>
"""
    
    # Add each category
    for category, signals in scan_results.items():
        html += f"""
        <div class="category">
            <div class="category-title">{category}</div>
"""
        
        if not signals:
            html += """
            <div class="no-signals">
                <p>📊 No active symbols found in this category</p>
            </div>
"""
        else:
            # Show top 5 or all signals
            for sig in signals[:5]:
                badge_class = "buy-badge" if sig['signal'] == 'BUY' else "sell-badge" if sig['signal'] == 'SELL' else "hold-badge"
                action_text = sig['signal'] if sig['signal'] else "HOLD"
                
                change_color = "#10b981" if sig['change_24h'] >= 0 else "#ef4444"
                
                html += f"""
            <div class="signal-card">
                <div class="signal-header">
                    <div class="symbol-name">{sig['symbol']}</div>
                    {f'<div class="action-badge {badge_class}">{action_text}</div>' if sig['signal'] else ''}
                </div>
                
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-label">Current Price</div>
                        <div class="metric-value">{sig['price']:.5f}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">24h Change</div>
                        <div class="metric-value" style="color: {change_color}">{sig['change_24h']:+.2f}%</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Trend</div>
                        <div class="metric-value" style="font-size: 14px;">{sig['trend']}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Volatility</div>
                        <div class="metric-value" style="font-size: 14px;">{sig['risk']}</div>
                    </div>
                </div>
"""
                
                if sig['signal']:
                    html += f"""
                <div class="trade-plan">
                    <div class="trade-plan-title">📋 Suggested Trade Plan</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 13px;">
                        <div><strong>Entry:</strong> {sig['price']:.5f}</div>
                        <div><strong>R:R Ratio:</strong> 1:{sig['rr_ratio']:.1f}</div>
                        <div style="color: #dc2626;"><strong>Stop Loss:</strong> {sig['sl']:.5f}</div>
                        <div style="color: #059669;"><strong>Take Profit:</strong> {sig['tp']:.5f}</div>
                    </div>
                    <div style="margin-top: 10px; font-size: 12px; color: #64748b;">
                        <em>SL/TP calculated using 1.5x and 3.0x ATR ({sig['atr']:.5f})</em>
                    </div>
                </div>
"""
                
                html += """
            </div>
"""
    
    html += f"""
        </div>
        
        <div class="footer">
            <p><strong>Titan AI Trading System</strong></p>
            <p>Powered by Neural Networks & Genetic Algorithms</p>
            <p>This report contains {sum(len(signals) for signals in scan_results.values())} analyzed symbols</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    scanner = MultiCategoryScanner()
    results = scanner.scan_all_categories()
    
    # Generate report
    html_report = generate_html_report(results)
    
    # Save locally
    with open("multi_category_report.html", "w", encoding="utf-8") as f:
        f.write(html_report)
    
    print("\n✅ Report saved to multi_category_report.html")
    
    # Send email
    from notification import EmailNotification
    notifier = EmailNotification()
    subject = f"🎯 Multi-Category Trading Signals - {datetime.now().strftime('%B %d, %Y')}"
    notifier.send_email(subject, html_report)
    print("✅ Email sent!")
