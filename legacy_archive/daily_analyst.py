import pandas as pd
import numpy as np
import datetime
from core.mt5_interface import MT5Interface
from core.market_scanner import MarketScanner
from core.strategy import Strategy
from notification import EmailNotification
# import mt5_interface as mt5_constants  <-- Removed broken import
# Note: mt5_interface module imports MetaTrader5 as mt5 internally but doesn't expose constants directly 
# unless we import them or the module re-exports. 
# We'll use the TIMEFRAME from main or just hardcode/import mt5
import MetaTrader5 as mt5

class DailyAnalyst:
    def __init__(self):
        self.scanner = MarketScanner()
        self.interface = MT5Interface()
        self.notifier = EmailNotification()
        self.timeframe = mt5.TIMEFRAME_H1 # Default analysis timeframe

    def run_daily_analysis(self):
        """
        Orchestrates the daily analysis flow:
        1. Connect
        2. Deep Scan (includes Analysis & Reasoning)
        3. Generate AI Commentary
        4. Generate Report
        5. Email
        """
        print("Starting Deep Reasoning Daily Analysis...")
        if not self.interface.start():
            print("Failed to start MT5 for analysis.")
            return

        # 1. Deep Scan
        # Includes Strategy run, ATR calc, Signal generation, and Reasoning
        print("Running Deep Market Scan (Forex, Metals, Crypto)...")
        scan_results = self.scanner.scan(max_spread=50)
        
        # Accepted trades
        signals = scan_results['accepted']
        
        # Rejected "Near Misses" for context
        rejected = scan_results['rejected']

        print(f"Analysis Complete. Found {len(signals)} opportunities.")

        # 2. Generate AI Commentary
        # We pass the full signal objects which now contain 'why' text
        ai_commentary = self._generate_gemini_commentary(signals, rejected)
        
        # 3. Generate HTML with AI text
        html_content = self._generate_html_report(signals, rejected, ai_commentary)
        
        # 4. Send Email
        subject = f"Market Intelligence Report - {datetime.datetime.now().strftime('%Y-%m-%d')}"
        self.notifier.send_email(subject, html_content)
        
        print("Daily Analysis Complete and Email Sent.")

    def _generate_gemini_commentary(self, signals, movers):
        """
        Uses Google Gemini to write a professional hedge fund summary.
        """
        try:
            import google.generativeai as genai
            import config
            
            if not hasattr(config, 'GOOGLE_API_KEY') or not config.GOOGLE_API_KEY:
                return "The markets are moving. Our algorithms are monitoring for breakout opportunities in major pairs."
                
            genai.configure(api_key=config.GOOGLE_API_KEY)
            
            # Model Cascade Strategy
            models_to_try = [
                'gemini-2.5-flash',
                'gemini-2.5-flash-lite',
                'gemini-1.5-flash',
                'gemini-pro'
            ]
            
            # Construct Prompt (same for all)
            data_summary = f"Signals: {len(signals)} found. "
            if signals:
                data_summary += f"Top signal: {signals[0]['symbol']} ({signals[0]['signal']}). "
            
            # Use rejected list context instead of movers if using rejected
            valid_movers = [m for m in movers if 'change' in m]
            if valid_movers:
                top_movers = ", ".join([f"{m['symbol']} ({m['change']:+.2f}%)" for m in valid_movers[:3]])
                data_summary += f"Major Movers: {top_movers}."
            else:
                 data_summary += f"Rejected Ideas: {len(movers)} (mostly spread/filter)."
            
            prompt = f"""
            You are a senior hedge fund portfolio manager writing a detailed weekly strategic outlook.
            
            Key Signals Detected:
            {data_summary}
            
            YOUR TASK:
            1. Analyze the context. Why are these signals happening? (e.g., Inflation data, Tech rally, Safe-haven flows).
            2. Pick the BEST signal from the list and explain the trade setup. 
               - Explain WHY the Stop Loss and Take Profit makes sense (Volatility-based).
               - Explain WHY we chose the specific strategy style (Scalp vs Swing).
            3. Provide a brief "Risk Warning".
            
            Tone: Professional, Insightful, yet easy to understand. Max 150 words.
            """
            
            # Attempt generation with fallback
            for model_name in models_to_try:
                try:
                    print(f"   👉 Asking AI ({model_name})...", end=" ")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    print("✅ Success!")
                    return response.text
                except Exception as e:
                    print(f"❌ Failed ({e}). Trying next...")
                    continue
            
            return "Global markets are showing mixed signals. Our AI could not reach the server, but technical signals remain valid."

        except Exception as e:
            print(f"Gemini generation failed: {e}")
            return "Global markets are showing mixed signals today. Volatility is creating opportunities in select currency pairs."

    def _generate_html_report(self, signals, rejected, commentary):
        """
        Creates a beautiful HTML email body with Deep Reasoning.
        """
        
        # HTML Helper functions
        def color_change(val):
            return "#4ade80" if val >= 0 else "#f87171" # Green : Red
            
        def signal_badge(sig):
            color = "#10b981" if sig == 'BUY' else "#ef4444"
            icon = "📈" if sig == 'BUY' else "📉"
            return f'<span style="background-color: {color}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; display: inline-block;">{icon} {sig}</span>'

        # Main Template
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f4f6; color: #1f2937; margin: 0; padding: 0; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
            .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 26px; font-weight: 800; letter-spacing: 1px; }}
            .header p {{ margin: 10px 0 0; opacity: 0.8; font-size: 14px; text-transform: uppercase; }}
            .content {{ padding: 30px; }}
            
            .section-title {{ font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 20px; border-bottom: 3px solid #e2e8f0; padding-bottom: 8px; display: flex; align-items: center; letter-spacing: -0.5px; }}
            
            .ai-box {{ background-color: #eff6ff; border-left: 5px solid #3b82f6; padding: 20px; border-radius: 0 6px 6px 0; color: #1e3a8a; font-size: 15px; line-height: 1.6; margin-bottom: 30px; }}
            
            /* Card Style for Signals */
            .signal-card {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; margin-bottom: 20px; transition: transform 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }}
            .signal-header {{ padding: 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }}
            .signal-body {{ padding: 15px; }}
            .signal-footer {{ padding: 10px 15px; background: #f1f5f9; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b; font-style: italic; }}
            
            .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 15px; }}
            .metric-box {{ background: #f8fafc; padding: 8px; border-radius: 4px; border: 1px solid #edeff2; }}
            .metric-label {{ font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 700; }}
            .metric-value {{ font-size: 14px; font-weight: 600; color: #0f172a; }}
            
            .why-box {{ background: #fffbeb; border: 1px solid #fcd34d; color: #92400e; padding: 10px; border-radius: 6px; font-size: 13px; margin-bottom: 15px; line-height: 1.5; }}
            
            .rejected-table {{ width: 100%; font-size: 13px; border-collapse: collapse; }}
            .rejected-table th {{ text-align: left; padding: 8px; background: #f1f5f9; color: #64748b; border-bottom: 2px solid #e2e8f0; }}
            .rejected-table td {{ padding: 8px; border-bottom: 1px solid #e2e8f0; }}
            
            .footer {{ background-color: #f8fafc; padding: 20px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; }}
        </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Titan Active Intelligence</h1>
                    <p>Deep Reasoning Report • {datetime.datetime.now().strftime('%d %b %Y')}</p>
                </div>
                
                <div class="content">
                    <div class="section-title">🧠 AI Strategy Rationale</div>
                    <div class="ai-box">
                        {commentary}
                    </div>
        """

        if signals:
            html += """
                    <div class="section-title">⚡ High-Probability Trade Plans</div>
            """
            for s in signals:
                # Calculate color for P&L
                pnl = s.get('financials', {}).get('projected_profit', 0)
                risk = s.get('financials', {}).get('projected_loss', 0)
                
                html += f"""
                <div class="signal-card">
                    <div class="signal-header">
                        <div>
                            <span style="font-size: 18px; font-weight: 800; color: #0f172a;">{s['symbol']}</span>
                            <span style="font-size: 12px; color: #64748b; margin-left: 10px;">{s['category']}</span>
                        </div>
                        {signal_badge(s['signal'])}
                    </div>
                    
                    <div class="signal-body">
                        <!-- THE WHY -->
                        <div class="why-box">
                            <strong>💡 Why we are taking this:</strong> {s.get('why', 'Technical criteria met.')}
                        </div>
                        
                        <!-- METRICS GRID -->
                        <div class="metric-grid">
                            <div class="metric-box">
                                <div class="metric-label">Entry</div>
                                <div class="metric-value">{s['entry']:.5f}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Stop Loss</div>
                                <div class="metric-value" style="color: #ef4444;">{s['sl']:.5f}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Take Profit</div>
                                <div class="metric-value" style="color: #10b981;">{s['tp']:.5f}</div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Volatility (ATR)</div>
                                <div class="metric-value">{s['atr']:.5f}</div>
                            </div>
                             <div class="metric-box">
                                <div class="metric-label">Proj. Profit (0.1 Lot)</div>
                                <div class="metric-value" style="color: #10b981;">${pnl:,.2f}</div>
                            </div>
                             <div class="metric-box">
                                <div class="metric-label">Risk (0.1 Lot)</div>
                                <div class="metric-value" style="color: #ef4444;">-${risk:,.2f}</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="signal-footer">
                        Strategy: <strong>{s.get('style', 'SWING')}</strong> • Risk/Reward: <strong>1:{s.get('financials', {}).get('rr_ratio', 0):.1f}</strong>
                    </div>
                </div>
                """
        else:
            html += """
            <div style="text-align: center; padding: 40px; color: #64748b; border: 2px dashed #e2e8f0; border-radius: 8px;">
                <h3>🛡️ Capital Preservation Mode</h3>
                <p>No high-probability setups found. Volatility undefined.</p>
            </div>
            """

        if rejected:
            html += """
                    <div class="section-title">🛑 Rejected Opportunities (Why we said NO)</div>
                    <table class="rejected-table">
                         <thead><tr><th>Symbol</th><th>Reason</th><th>Metric</th></tr></thead>
                         <tbody>
            """
            for r in rejected[:8]: # Show top 8 rejections
                metric_text = ""
                if 'data' in r:
                    if r['reason_code'] == 'RSI_OVERBOUGHT':
                        metric_text = f"RSI: {r['data'].get('rsi', 0):.1f}"
                    elif r['reason_code'] == 'SPREAD_TOO_HIGH':
                        metric_text = f"Spread: {r['data'].get('spread')}"
                    else:
                        metric_text = "-"
                        
                html += f"""
                        <tr>
                            <td><strong>{r['symbol']}</strong></td>
                            <td>{r['reason_text']}</td>
                            <td><code style="font-size: 11px; color: #dc2626;">{metric_text}</code></td>
                        </tr>
                """
            html += """
                        </tbody>
                    </table>
            """

        html += f"""
                    <div class="section-title">💡 System Status</div>
                    <p style="font-size: 14px; color: #4b5563;">
                        Scanned {len(signals) + len(rejected)} relevant symbols across {len(set([s['category'] for s in signals] if signals else []))} categories.
                    </p>
                </div>
                
                <div class="footer">
                    <p>Generated by Titan Active Intelligence</p>
                    <p>Deep Reasoning Engine v2.0 • {datetime.datetime.now().strftime('%H:%M %Z')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

if __name__ == "__main__":
    analyst = DailyAnalyst()
    analyst.run_daily_analysis()
