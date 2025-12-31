import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import settings
from titan_system.math_core.regression import LinearRegressionChannel
from titan_system.math_core.statistics import StatisticalMetrics
from titan_system.db.database import Database
from titan_system.notifications.email import EmailNotifier
from jinja2 import Environment, FileSystemLoader
import os
from datetime import datetime

def scan_and_email():
    """Scan all markets and send opportunities via email"""
    
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
        
    db = Database(settings.db_path)
    symbols = db.get_active_universe(limit=50)
    
    print(f"\n🔍 Scanning {len(symbols)} markets...")
    
    opportunities = []
    reg = LinearRegressionChannel(period=100)

    for symbol in symbols:
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
            if rates is None or len(rates) < 150:
                continue
                
            df = pd.DataFrame(rates)
            closes = df['close'].values
            
            # Calculate metrics
            stats = reg.calculate(closes)
            expected = stats['slope'] * np.arange(len(closes)) + stats['intercept']
            residuals = closes[-100:] - expected[-100:]
            half_life = StatisticalMetrics.calculate_half_life(residuals)
            
            z = stats['z_score']
            
            # Determine signal
            signal = "HOLD"
            if z > 2.0 and half_life < 25:
                signal = "SELL"
            elif z < -2.0 and half_life < 25:
                signal = "BUY"
            
            opportunities.append({
                "symbol": symbol,
                "price": closes[-1],
                "z_score": z,
                "half_life": half_life,
                "signal": signal,
                "fair_value": stats['expected_price'],
                "std_dev": stats['std_dev'],
                "probability": 95 if abs(z) >= 2.0 else 68 if abs(z) >= 1.0 else 50
            })
            
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")
            continue
            
    mt5.shutdown()
    
    # Sort by signal quality (extreme Z-scores first)
    opportunities.sort(key=lambda x: abs(x['z_score']), reverse=True)
    
    # Separate by signal type
    buy_opps = [o for o in opportunities if o['signal'] == 'BUY']
    sell_opps = [o for o in opportunities if o['signal'] == 'SELL']
    neutral = [o for o in opportunities if o['signal'] == 'HOLD']
    
    print(f"✅ Scan complete: {len(buy_opps)} BUY | {len(sell_opps)} SELL | {len(neutral)} NEUTRAL")
    
    # Generate and send email
    send_opportunities_email(buy_opps, sell_opps, neutral[:10])  # Top 10 neutral
    
def send_opportunities_email(buy_opps, sell_opps, neutral):
    """Send formatted email with all opportunities"""
    
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'titan_system', 'notifications', 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Create HTML email
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Inter', system-ui, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: linear-gradient(135deg, #1a1f2e 0%, #111827 100%);
            border-radius: 16px;
            padding: 32px;
            box-shadow: 0 20px 50px rgba(0,0,0,0.7);
        }}
        h1 {{
            font-size: 32px;
            margin: 0 0 8px 0;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .timestamp {{
            color: #6b7280;
            font-size: 14px;
            margin-bottom: 32px;
        }}
        .section {{
            margin-bottom: 32px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .buy-title {{ color: #34d399; }}
        .sell-title {{ color: #f87171; }}
        .neutral-title {{ color: #9ca3af; }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
        }}
        th {{
            background: rgba(0,0,0,0.3);
            padding: 12px;
            text-align: left;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: #9ca3af;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
            font-size: 14px;
        }}
        tr:hover {{
            background: rgba(255,255,255,0.02);
        }}
        .symbol {{
            font-weight: 700;
            color: #fff;
        }}
        .z-positive {{ color: #f87171; }}
        .z-negative {{ color: #34d399; }}
        .prob-high {{ color: #34d399; font-weight: 700; }}
        .prob-med {{ color: #fbbf24; }}
        .footer {{
            text-align: center;
            margin-top: 32px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: #6b7280;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Daily Market Opportunities</h1>
        <div class="timestamp">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        
        <div class="section">
            <div class="section-title buy-title">🟢 BUY Opportunities ({len(buy_opps)})</div>
            {generate_table(buy_opps, 'BUY') if buy_opps else '<p style="color: #6b7280;">No strong buy setups at this time.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title sell-title">🔴 SELL Opportunities ({len(sell_opps)})</div>
            {generate_table(sell_opps, 'SELL') if sell_opps else '<p style="color: #6b7280;">No strong sell setups at this time.</p>'}
        </div>
        
        <div class="section">
            <div class="section-title neutral-title">⚪ Watching (Top 10 Neutral)</div>
            {generate_table(neutral, 'NEUTRAL') if neutral else '<p style="color: #6b7280;">All markets showing signals.</p>'}
        </div>
        
        <div class="footer">
            <strong>Titan Quantitative Scanner</strong><br>
            Powered by Statistical Arbitrage • Z-Score Analysis • Mean Reversion
        </div>
    </div>
</body>
</html>
"""
    
    notifier = EmailNotifier()
    notifier._send_email(
        subject=f"📊 Market Scanner: {len(buy_opps)} BUY | {len(sell_opps)} SELL Opportunities",
        html_message=html_content
    )
    print("✅ Opportunities email sent!")

def generate_table(opportunities, signal_type):
    """Generate HTML table for opportunities"""
    if not opportunities:
        return ""
    
    rows = []
    for opp in opportunities[:15]:  # Top 15 per category
        z_class = 'z-negative' if opp['z_score'] < 0 else 'z-positive'
        prob_class = 'prob-high' if opp['probability'] >= 95 else 'prob-med'
        
        rows.append(f"""
        <tr>
            <td class="symbol">{opp['symbol']}</td>
            <td>{opp['price']:.5f}</td>
            <td>{opp['fair_value']:.5f}</td>
            <td class="{z_class}">{opp['z_score']:.2f}σ</td>
            <td>{opp['half_life']:.1f} bars</td>
            <td class="{prob_class}">{opp['probability']}%</td>
        </tr>
        """)
    
    return f"""
    <table>
        <thead>
            <tr>
                <th>Symbol</th>
                <th>Price</th>
                <th>Fair Value</th>
                <th>Z-Score</th>
                <th>Half-Life</th>
                <th>Probability</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """

if __name__ == "__main__":
    scan_and_email()
