"""
Titan Trading Dashboard - Simple HTML Version
==============================================
Generates an HTML dashboard and opens it in browser.
Run with: python titan_dashboard_html.py
"""

import MetaTrader5 as mt5
import pandas as pd
import webbrowser
import os
from datetime import datetime, timedelta
import json

def generate_dashboard():
    """Generate HTML dashboard from MT5 data."""
    
    if not mt5.initialize():
        print("Failed to connect to MT5")
        return
    
    # Get data
    acc = mt5.account_info()
    positions = mt5.positions_get()
    
    # Get trade history
    from_date = datetime.now() - timedelta(days=30)
    deals = mt5.history_deals_get(from_date, datetime.now())
    
    # Calculate metrics
    if deals:
        trades = [d for d in deals if d.profit != 0]
        total_trades = len(trades)
        winners = len([t for t in trades if t.profit > 0])
        losers = len([t for t in trades if t.profit < 0])
        win_rate = (winners / total_trades * 100) if total_trades > 0 else 0
        total_profit = sum(t.profit for t in trades if t.profit > 0)
        total_loss = abs(sum(t.profit for t in trades if t.profit < 0))
        net_pnl = sum(t.profit for t in trades)
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
    else:
        total_trades = winners = losers = 0
        win_rate = net_pnl = profit_factor = 0
    
    # Build positions table
    positions_html = ""
    if positions:
        for p in positions:
            direction = "BUY" if p.type == 0 else "SELL"
            pnl_class = "profit" if p.profit >= 0 else "loss"
            positions_html += f"""
            <tr>
                <td>{p.symbol}</td>
                <td>{direction}</td>
                <td>{p.volume}</td>
                <td>{p.price_open:.5f}</td>
                <td>{p.price_current:.5f}</td>
                <td class="{pnl_class}">${p.profit:,.2f}</td>
            </tr>
            """
    else:
        positions_html = "<tr><td colspan='6'>No open positions</td></tr>"
    
    total_open_pnl = sum(p.profit for p in positions) if positions else 0
    
    # Build trade history
    history_html = ""
    if deals:
        for d in list(deals)[-20:]:  # Last 20 trades
            if d.profit != 0:
                pnl_class = "profit" if d.profit >= 0 else "loss"
                history_html += f"""
                <tr>
                    <td>{datetime.fromtimestamp(d.time).strftime('%m-%d %H:%M')}</td>
                    <td>{d.symbol}</td>
                    <td class="{pnl_class}">${d.profit:,.2f}</td>
                </tr>
                """
    
    # Generate HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Titan Trading Dashboard</title>
        <meta http-equiv="refresh" content="30">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, sans-serif;
                background: linear-gradient(135deg, #0a0a1a 0%, #1a1a2e 100%);
                color: #fff;
                min-height: 100vh;
                padding: 20px;
            }}
            .container {{ max-width: 1400px; margin: 0 auto; }}
            h1 {{ 
                text-align: center; 
                margin-bottom: 30px;
                background: linear-gradient(90deg, #00ff88, #00d4ff);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                font-size: 2.5em;
            }}
            .metrics {{ 
                display: grid; 
                grid-template-columns: repeat(5, 1fr); 
                gap: 15px; 
                margin-bottom: 30px;
            }}
            .metric-card {{
                background: linear-gradient(135deg, #1a1a3e 0%, #2a2a4e 100%);
                padding: 20px;
                border-radius: 15px;
                text-align: center;
                border: 1px solid #3a3a5e;
            }}
            .metric-value {{ 
                font-size: 2em; 
                font-weight: bold;
                margin: 10px 0;
            }}
            .metric-label {{ color: #888; font-size: 0.9em; }}
            .profit {{ color: #00ff88; }}
            .loss {{ color: #ff4757; }}
            .section {{ 
                background: #1a1a2e;
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                border: 1px solid #2a2a4e;
            }}
            .section h2 {{ 
                margin-bottom: 15px;
                color: #00d4ff;
            }}
            table {{ 
                width: 100%; 
                border-collapse: collapse;
            }}
            th, td {{ 
                padding: 12px; 
                text-align: left; 
                border-bottom: 1px solid #2a2a4e;
            }}
            th {{ background: #2a2a4e; color: #00d4ff; }}
            tr:hover {{ background: #2a2a3e; }}
            .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            .timestamp {{ text-align: center; color: #666; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Titan Trading Dashboard</h1>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-label">Balance</div>
                    <div class="metric-value">${acc.balance:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Equity</div>
                    <div class="metric-value">${acc.equity:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Open P&L</div>
                    <div class="metric-value {'profit' if total_open_pnl >= 0 else 'loss'}">${total_open_pnl:,.2f}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Win Rate</div>
                    <div class="metric-value">{win_rate:.1f}%</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value">{profit_factor:.2f}</div>
                </div>
            </div>
            
            <div class="grid">
                <div class="section">
                    <h2>📈 Open Positions</h2>
                    <table>
                        <tr>
                            <th>Symbol</th>
                            <th>Type</th>
                            <th>Volume</th>
                            <th>Entry</th>
                            <th>Current</th>
                            <th>P&L</th>
                        </tr>
                        {positions_html}
                    </table>
                </div>
                
                <div class="section">
                    <h2>📋 Recent Trades</h2>
                    <table>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>P&L</th>
                        </tr>
                        {history_html}
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>📊 Performance Summary (30 Days)</h2>
                <div class="metrics" style="grid-template-columns: repeat(4, 1fr);">
                    <div class="metric-card">
                        <div class="metric-label">Total Trades</div>
                        <div class="metric-value">{total_trades}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Winners</div>
                        <div class="metric-value profit">{winners}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Losers</div>
                        <div class="metric-value loss">{losers}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Net P&L</div>
                        <div class="metric-value {'profit' if net_pnl >= 0 else 'loss'}">${net_pnl:,.2f}</div>
                    </div>
                </div>
            </div>
            
            <div class="timestamp">
                Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Auto-refreshes every 30 seconds
            </div>
        </div>
    </body>
    </html>
    """
    
    # Save to file
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard generated: {output_path}")
    webbrowser.open(f'file://{output_path}')
    
    mt5.shutdown()

if __name__ == "__main__":
    generate_dashboard()
