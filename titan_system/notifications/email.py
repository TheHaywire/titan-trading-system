
from config.settings import settings
import requests
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

logger = logging.getLogger("Titan.Notifications")

class EmailNotifier:
    def __init__(self):
        self.service_id = settings.emailjs_service_id
        self.template_id = settings.emailjs_template_id
        self.public_key = settings.emailjs_public_key
        self.user_email = settings.emailjs_user_email
        self.api_url = "https://api.emailjs.com/api/v1.0/email/send"
        
        # Setup Jinja2 for templates
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

    def send_trade_alert(self, trade_data: dict, market_analysis: dict = None):
        """Sends an instant alert for a new trade execution."""
        if not settings.enable_email_notifications:
            return

        try:
            # Extract Quant Metrics from strategy analysis
            quant_metrics = {}
            if market_analysis:
                # Check if there are metrics from RegressionSurfer
                metrics = market_analysis.get('metrics', {})
                if metrics:
                    z_score = metrics.get('z_score')
                    half_life = metrics.get('half_life')
                    fair_value = metrics.get('expected_price')
                    
                    if z_score is not None:
                        quant_metrics = {
                            'z_score': f"{z_score:.2f}",
                            'half_life': f"{half_life:.1f}" if half_life else "N/A",
                            'fair_value': f"{fair_value:.5f}" if fair_value else "N/A",
                            'probability': "95" if abs(z_score) >= 2.0 else "68" if abs(z_score) >= 1.0 else "N/A"
                        }
                        
                        # Generate quant explanation
                        if z_score > 2.0:
                            quant_metrics['quant_reason'] = f"Price is <strong>+{abs(z_score):.1f} standard deviations</strong> above fair value ({fair_value:.5f}). Statistically overbought with {quant_metrics['probability']}% probability of mean reversion within {half_life:.0f} bars."
                        elif z_score < -2.0:
                            quant_metrics['quant_reason'] = f"Price is <strong>-{abs(z_score):.1f} standard deviations</strong> below fair value ({fair_value:.5f}). Statistically oversold with {quant_metrics['probability']}% probability of mean reversion within {half_life:.0f} bars."
                        else:
                            quant_metrics['quant_reason'] = f"Price deviation is <strong>{z_score:.1f}σ</strong> from fair value. Half-life of {half_life:.0f} bars indicates fast mean-reversion dynamics."

            # Parse AI Insight if available
            ai_data = {}
            if market_analysis:
                ai_insight = market_analysis.get('ai_insight')
                if ai_insight:
                    try:
                        import json
                        if isinstance(ai_insight, str):
                            ai_data = json.loads(ai_insight)
                        else:
                            ai_data = ai_insight
                    except:
                        pass

            template = self.env.get_template('trade_alert.html')
            html_content = template.render(
                symbol=trade_data.get('symbol'),
                action=trade_data.get('type'),
                price=trade_data.get('open_price', trade_data.get('price')),
                time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                strategy=trade_data.get('strategy_name', trade_data.get('comment', 'Titan System')),
                score=market_analysis.get('score') if market_analysis else None,
                # Quant Metrics
                **quant_metrics,
                # AI Data
                ai_summary=ai_data.get('summary'),
                ai_tp1=ai_data.get('trade_setup', {}).get('take_profit_1'),
                ai_sl=ai_data.get('trade_setup', {}).get('stop_loss')
            )
            
            self._send_email(
                subject=f"🚀 Trade Executed: {trade_data.get('symbol')} {trade_data.get('type')}",
                html_message=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send trade alert: {e}")

    def send_daily_report(self, stats: dict):
        """Sends the daily profit/loss report."""
        if not settings.enable_email_notifications:
            return

        try:
            template = self.env.get_template('daily_report.html')
            html_content = template.render(
                date=datetime.now().strftime("%Y-%m-%d"),
                total_profit=stats.get('total_profit', 0.0),
                trades_count=stats.get('trades_count', 0),
                win_rate=stats.get('win_rate', 0.0),
                balance=stats.get('balance', 0.0),
                equity=stats.get('equity', 0.0)
            )
            
            emoji = "💰" if stats.get('total_profit', 0) >= 0 else "🔻"
            self._send_email(
                subject=f"{emoji} Titan Daily Report: ${stats.get('total_profit', 0.0):.2f}",
                html_message=html_content
            )
        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")

    def _send_email(self, subject: str, html_message: str):
        """Internal method to send email via EmailJS."""
        payload = {
            "service_id": self.service_id,
            "template_id": self.template_id,
            "user_id": self.public_key,
            "accessToken": settings.emailjs_private_key,
            "template_params": {
                "to_email": self.user_email,
                "subject": subject,
                "message": html_message,  # Note: Template in EmailJS must look for {{message}} or be HTML enabled
                "html_content": html_message # Redundant key just in case
            }
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            if response.status_code == 200:
                logger.info(f"📧 Email sent: {subject}")
            else:
                logger.error(f"EmailJS Error: {response.text}")
        except Exception as e:
            logger.error(f"Email Connection Error: {e}")
