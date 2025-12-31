"""
Titan Trading Dashboard - Prop Firm Style
==========================================
Visual trading journal and analytics dashboard.
Run with: streamlit run titan_dashboard.py
"""

import streamlit as st
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="Titan Trading Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for prop-firm style
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #0f3460;
    }
    .profit { color: #00ff88; }
    .loss { color: #ff4757; }
    .stMetric { background: #1a1a2e; padding: 10px; border-radius: 8px; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

# Initialize MT5
def init_mt5():
    if not mt5.initialize():
        return False
    return True

# Get account info
def get_account_info():
    acc = mt5.account_info()
    if acc:
        return {
            'balance': acc.balance,
            'equity': acc.equity,
            'profit': acc.profit,
            'margin': acc.margin,
            'free_margin': acc.margin_free,
            'margin_level': acc.margin_level if acc.margin_level else 0
        }
    return None

# Get positions
def get_positions():
    positions = mt5.positions_get()
    if not positions:
        return pd.DataFrame()
    
    data = []
    for p in positions:
        data.append({
            'Ticket': p.ticket,
            'Symbol': p.symbol,
            'Type': 'BUY' if p.type == 0 else 'SELL',
            'Volume': p.volume,
            'Entry': p.price_open,
            'Current': p.price_current,
            'SL': p.sl,
            'TP': p.tp,
            'P&L': p.profit,
            'Swap': p.swap,
            'Time': datetime.fromtimestamp(p.time)
        })
    return pd.DataFrame(data)

# Get trade history
def get_trade_history(days=30):
    from_date = datetime.now() - timedelta(days=days)
    deals = mt5.history_deals_get(from_date, datetime.now())
    if not deals:
        return pd.DataFrame()
    
    data = []
    for d in deals:
        if d.profit != 0:  # Only trades with P&L
            data.append({
                'Time': datetime.fromtimestamp(d.time),
                'Symbol': d.symbol,
                'Type': 'BUY' if d.type == 0 else 'SELL',
                'Volume': d.volume,
                'Price': d.price,
                'P&L': d.profit,
                'Commission': d.commission,
                'Swap': d.swap
            })
    return pd.DataFrame(data)

# Calculate metrics
def calculate_metrics(history_df):
    if history_df.empty:
        return {}
    
    total_trades = len(history_df)
    winning_trades = len(history_df[history_df['P&L'] > 0])
    losing_trades = len(history_df[history_df['P&L'] < 0])
    
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    total_profit = history_df[history_df['P&L'] > 0]['P&L'].sum()
    total_loss = abs(history_df[history_df['P&L'] < 0]['P&L'].sum())
    profit_factor = total_profit / total_loss if total_loss > 0 else 0
    
    avg_win = history_df[history_df['P&L'] > 0]['P&L'].mean() if winning_trades > 0 else 0
    avg_loss = abs(history_df[history_df['P&L'] < 0]['P&L'].mean()) if losing_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'profit_factor': profit_factor,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'net_pnl': history_df['P&L'].sum()
    }

# Main app
def main():
    if not init_mt5():
        st.error("❌ Failed to connect to MT5. Please ensure MT5 is running.")
        return
    
    # Sidebar
    st.sidebar.title("🎯 Titan Dashboard")
    st.sidebar.markdown("---")
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=False)
    if auto_refresh:
        st.rerun()
    
    history_days = st.sidebar.slider("History Days", 7, 90, 30)
    
    # Get data
    account = get_account_info()
    positions_df = get_positions()
    history_df = get_trade_history(history_days)
    metrics = calculate_metrics(history_df)
    
    # Header
    st.title("📊 Titan Trading Dashboard")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Account Overview
    st.header("💰 Account Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    if account:
        with col1:
            st.metric("Balance", f"${account['balance']:,.2f}")
        with col2:
            st.metric("Equity", f"${account['equity']:,.2f}")
        with col3:
            pnl_color = "normal" if account['profit'] >= 0 else "inverse"
            st.metric("Open P&L", f"${account['profit']:,.2f}", 
                     delta=f"{account['profit']/account['balance']*100:.2f}%" if account['balance'] > 0 else "0%",
                     delta_color=pnl_color)
        with col4:
            st.metric("Margin Used", f"${account['margin']:,.2f}")
        with col5:
            margin_pct = account['margin'] / account['balance'] * 100 if account['balance'] > 0 else 0
            st.metric("Margin Level", f"{account['margin_level']:.0f}%")
    
    st.markdown("---")
    
    # Two columns: Positions and Metrics
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.header("📈 Open Positions")
        if not positions_df.empty:
            # Color code P&L
            def color_pnl(val):
                color = '#00ff88' if val > 0 else '#ff4757' if val < 0 else 'white'
                return f'color: {color}'
            
            styled_df = positions_df.style.applymap(color_pnl, subset=['P&L'])
            st.dataframe(styled_df, use_container_width=True, height=300)
            
            # Summary
            total_pnl = positions_df['P&L'].sum()
            total_lots = positions_df['Volume'].sum()
            st.markdown(f"**Total Open P&L:** :{'green' if total_pnl >= 0 else 'red'}[${total_pnl:,.2f}] | **Total Lots:** {total_lots:.2f}")
        else:
            st.info("No open positions")
    
    with col_right:
        st.header("📊 Performance Metrics")
        if metrics:
            st.metric("Win Rate", f"{metrics['win_rate']:.1f}%")
            st.metric("Total Trades", metrics['total_trades'])
            st.metric("Profit Factor", f"{metrics['profit_factor']:.2f}")
            st.metric("Avg Win", f"${metrics['avg_win']:.2f}")
            st.metric("Avg Loss", f"${metrics['avg_loss']:.2f}")
            st.metric(f"Net P&L ({history_days}d)", f"${metrics['net_pnl']:,.2f}")
        else:
            st.info("No trade history")
    
    st.markdown("---")
    
    # Charts
    st.header("📉 Performance Charts")
    
    if not history_df.empty:
        tab1, tab2, tab3 = st.tabs(["Equity Curve", "Daily P&L", "Symbol Performance"])
        
        with tab1:
            # Cumulative P&L
            history_df_sorted = history_df.sort_values('Time')
            history_df_sorted['Cumulative'] = history_df_sorted['P&L'].cumsum()
            
            fig = px.line(history_df_sorted, x='Time', y='Cumulative', 
                         title='Cumulative P&L (Equity Curve)')
            fig.update_traces(line_color='#00ff88')
            fig.update_layout(
                template='plotly_dark',
                xaxis_title='Date',
                yaxis_title='P&L ($)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab2:
            # Daily P&L
            history_df['Date'] = history_df['Time'].dt.date
            daily_pnl = history_df.groupby('Date')['P&L'].sum().reset_index()
            
            colors = ['#00ff88' if x >= 0 else '#ff4757' for x in daily_pnl['P&L']]
            
            fig = go.Figure(data=[
                go.Bar(x=daily_pnl['Date'], y=daily_pnl['P&L'], marker_color=colors)
            ])
            fig.update_layout(
                title='Daily P&L',
                template='plotly_dark',
                xaxis_title='Date',
                yaxis_title='P&L ($)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Symbol performance
            symbol_pnl = history_df.groupby('Symbol').agg({
                'P&L': ['sum', 'count', 'mean']
            }).reset_index()
            symbol_pnl.columns = ['Symbol', 'Total P&L', 'Trades', 'Avg P&L']
            symbol_pnl = symbol_pnl.sort_values('Total P&L', ascending=False)
            
            colors = ['#00ff88' if x >= 0 else '#ff4757' for x in symbol_pnl['Total P&L']]
            
            fig = go.Figure(data=[
                go.Bar(x=symbol_pnl['Symbol'], y=symbol_pnl['Total P&L'], marker_color=colors)
            ])
            fig.update_layout(
                title='P&L by Symbol',
                template='plotly_dark',
                xaxis_title='Symbol',
                yaxis_title='P&L ($)'
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trade history to display")
    
    st.markdown("---")
    
    # Trade History
    st.header("📋 Trade History")
    if not history_df.empty:
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            symbols = ['All'] + list(history_df['Symbol'].unique())
            selected_symbol = st.selectbox("Filter by Symbol", symbols)
        with col2:
            trade_type = st.selectbox("Filter by Type", ['All', 'Winners', 'Losers'])
        
        # Apply filters
        filtered_df = history_df.copy()
        if selected_symbol != 'All':
            filtered_df = filtered_df[filtered_df['Symbol'] == selected_symbol]
        if trade_type == 'Winners':
            filtered_df = filtered_df[filtered_df['P&L'] > 0]
        elif trade_type == 'Losers':
            filtered_df = filtered_df[filtered_df['P&L'] < 0]
        
        st.dataframe(filtered_df.sort_values('Time', ascending=False), use_container_width=True)
        
        # Export
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"trade_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No trade history")
    
    # Footer
    st.markdown("---")
    st.markdown("*Titan Trading System v2.0 | Real-time MT5 Integration*")

if __name__ == "__main__":
    main()
