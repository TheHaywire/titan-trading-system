import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import './App.css'

const API_URL = 'http://localhost:8010'

function App() {
  const [activeTab, setActiveTab] = useState('command') // 'factory' or 'command'
  const [symbols, setSymbols] = useState([])
  const [portfolio, setPortfolio] = useState(null)
  const [alerts, setAlerts] = useState([])

  // Existing factory state
  const [fleetOverview, setFleetOverview] = useState(null)
  const [strategies, setStrategies] = useState([])
  const [equityCurve, setEquityCurve] = useState([])
  const [logs, setLogs] = useState([])
  const [marketPulse, setMarketPulse] = useState([])
  const [factoryStats, setFactoryStats] = useState(null)
  const [hotSymbols, setHotSymbols] = useState([])
  const [selectedStatus, setSelectedStatus] = useState('all')
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [apiStatus, setApiStatus] = useState('connecting')

  const terminalRef = useRef(null)

  useEffect(() => {
    fetchFactoryData()
    fetchCommandData()
    const interval = setInterval(() => {
      fetchFactoryData()
      fetchCommandData()
    }, 5000)
    return () => clearInterval(interval)
  }, [selectedStatus])

  const fetchFactoryData = async () => {
    const FACTORY_API = 'http://localhost:8000/api'
    try {
      const [ov, st, eq, lg, pulse, fStats, hot] = await Promise.all([
        fetch(`${FACTORY_API}/fleet/overview`).then(r => r.json()),
        fetch(`${FACTORY_API}/strategies${selectedStatus !== 'all' ? `?status=${selectedStatus}` : ''}`).then(r => r.json()),
        fetch(`${FACTORY_API}/performance/equity`).then(r => r.json()),
        fetch(`${FACTORY_API}/fleet/logs`).then(r => r.json()),
        fetch(`${FACTORY_API}/market/pulse`).then(r => r.json()),
        fetch(`${FACTORY_API}/factory/stats`).then(r => r.json()),
        fetch(`${FACTORY_API}/market/hot`).then(r => r.json())
      ])

      setFleetOverview(ov)
      setStrategies(st)
      setEquityCurve(eq.data || [])
      setLogs(lg.logs || [])
      setMarketPulse(pulse.pulse || [])
      setFactoryStats(fStats)
      setHotSymbols(hot || [])
      setApiStatus('connected')
    } catch (err) {
      console.error('Factory API error:', err)
    }
  }

  const fetchCommandData = async () => {
    try {
      const [syms, port, alrt] = await Promise.all([
        fetch(`${API_URL}/symbols`).then(r => r.json()),
        fetch(`${API_URL}/portfolio`).then(r => r.json()),
        fetch(`${API_URL}/alerts`).then(r => r.json())
      ])

      setSymbols(syms)
      setPortfolio(port)
      setAlerts(alrt || [])
      setLoading(false)
    } catch (err) {
      console.error('Command API error:', err)
    }
  }

  const retireStrategy = async (id) => {
    if (!confirm(`Confirm absolute retirement of Alpha node ${id.substring(0, 8)}?`)) return
    await fetch(`${API_URL}/control/retire/${id}`, { method: 'POST' })
    fetchAllData()
  }

  if (loading) return (
    <div className="loading-screen">
      <div className="terminal-loader">
        <p>&gt; INITIALIZING TITAN_SYSTEM_V2.0...</p>
        <p>&gt; CONNECTING TO MT5 BRIDGE...</p>
        <p>&gt; QUANT_LAB: SEARCHING FOR ALPHA...</p>
      </div>
    </div>
  )

  return (
    <div className="dashboard">
      <header className="header">
        <div className="logo-section">
          <h1>TITAN <span>ALPHA</span></h1>
          <p className="subtitle">Command & Control Intelligence v5.0</p>
        </div>
        <div className="tab-switcher">
          <button className={activeTab === 'command' ? 'active' : ''} onClick={() => setActiveTab('command')}>COMMAND_CENTER</button>
          <button className={activeTab === 'factory' ? 'active' : ''} onClick={() => setActiveTab('factory')}>ALPHA_FACTORY</button>
        </div>
        <div className="header-meta">
          <div className="status-indicator">
            <span className={`heartbeat ${apiStatus}`}></span>
            <span className="label">SYSTEM STATUS:</span>
            <span className="value">{apiStatus === 'connected' ? 'OPTIMAL' : 'OFFLINE'}</span>
          </div>
          <div className="last-sync">RECON_UTC: {new Date().toLocaleTimeString()}</div>
        </div>
      </header>

      {activeTab === 'command' ? (
        <div className="command-center-layout">
          {/* Market Overview Grid */}
          <div className="glass-panel command-grid">
            <div className="card-header">
              <h2>Market Overview Grid (MT5 + Finviz)</h2>
            </div>
            <table className="ultimate-table command-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Price</th>
                  <th>Change %</th>
                  <th>Rel Vol</th>
                  <th>Avg Vol</th>
                  <th>P/E</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {symbols.map(s => (
                  <tr key={s.ticker} className="row">
                    <td><span className="symbol">{s.ticker}</span></td>
                    <td className="numeric">${s.price?.toFixed(2)}</td>
                    <td className={`numeric ${s.change_pct >= 0 ? 'profit' : 'loss'}`}>
                      {s.change_pct?.toFixed(2)}%
                    </td>
                    <td className="numeric">{s.rel_vol?.toFixed(2)}x</td>
                    <td>{s.avg_vol}</td>
                    <td className="numeric">{s.pe?.toFixed(1) || '-'}</td>
                    <td><span className="type-badge">{s.source}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="command-side-columns">
            {/* Portfolio / Positions Panel */}
            <div className="glass-panel portfolio-panel">
              <div className="card-header">
                <h2>Live Portfolio (MT5)</h2>
              </div>
              <div className="account-summary">
                <div className="stat">
                  <span className="label">EQUITY</span>
                  <span className="val">${portfolio?.account?.equity?.toLocaleString()}</span>
                </div>
                <div className="stat">
                  <span className="label">FLOATING PNL</span>
                  <span className={`val ${portfolio?.account?.profit >= 0 ? 'profit' : 'loss'}`}>
                    ${portfolio?.account?.profit?.toFixed(2)}
                  </span>
                </div>
              </div>
              <div className="positions-list">
                {portfolio?.positions.map(p => (
                  <div key={p.ticket} className="pos-item">
                    <div className="pos-main">
                      <span className={`side ${p.type.toLowerCase()}`}>{p.type}</span>
                      <span className="sym">{p.symbol}</span>
                      <span className="vol">{p.volume} lots</span>
                    </div>
                    <div className={`pnl ${p.profit >= 0 ? 'profit' : 'loss'}`}>
                      ${p.profit.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Alert Engine Console */}
            <div className="glass-panel alerts-panel">
              <div className="card-header">
                <h2>Intelligence Alerts</h2>
              </div>
              <div className="alerts-list">
                {alerts.length > 0 ? alerts.map(a => (
                  <div key={a.id} className={`alert-item ${a.severity.toLowerCase()}`}>
                    <span className="time">{new Date(a.timestamp).toLocaleTimeString()}</span>
                    <span className="msg"><strong>{a.symbol_ticker}</strong>: {a.message}</span>
                  </div>
                )) : (
                  <div className="no-data">No active alerts... Monitoring regime.</div>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <>
          {/* Top Professional Stats Bar */}
          <div className="top-stats-bar glass-panel">
            <div className="stat-card active">
              <span className="label">Discovery Lane</span>
              <span className="value">{fleetOverview?.total_strategies || 0}</span>
            </div>
            <div className="stat-card">
              <span className="label">Validation Lab</span>
              <span className="value">{fleetOverview?.candidate_count || 0}</span>
            </div>
            <div className="stat-card">
              <span className="label">Deployed Alphas</span>
              <span className="value">{fleetOverview?.paper_count || 0}</span>
            </div>
            <div className="stat-card">
              <span className="label">Capital Nodes</span>
              <span className="value">{fleetOverview?.live_count || 0}</span>
            </div>
            <div className={`stat-card ${fleetOverview?.total_pnl >= 0 ? 'profit' : 'loss'}`}>
              <span className="label">Realized Yield</span>
              <span className="value">${fleetOverview?.total_pnl?.toFixed(2) || '0.00'}</span>
            </div>
            <div className="stat-card">
              <span className="label">SR Benchmark</span>
              <span className="value">{(fleetOverview?.paper_avg_sharpe || 0).toFixed(2)}</span>
            </div>
            <div className="stat-card">
              <span className="label">Uptime</span>
              <span className="value">{factoryStats?.factory_uptime}</span>
            </div>
          </div>

          <div className="main-grid">
            <div className="left-column">
              {/* Main Chart Card */}
              <div className="glass-panel chart-card">
                <div className="card-header">
                  <h2>Portfolio Value Matrix</h2>
                  <div className="chart-actions">
                    <button className="small-btn">1H</button>
                    <button className="small-btn active">4H</button>
                    <button className="small-btn">1D</button>
                  </div>
                </div>
                <div className="chart-container">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={equityCurve}>
                      <defs>
                        <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#00ffcc" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#00ffcc" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="timestamp" hide />
                      <YAxis hide domain={['auto', 'auto']} />
                      <Tooltip
                        contentStyle={{ background: '#0a0b10', border: '1px solid #333', borderRadius: '8px' }}
                        itemStyle={{ color: '#00ffcc' }}
                      />
                      <Area type="monotone" dataKey="equity" stroke="#00ffcc" strokeWidth={3} fillOpacity={1} fill="url(#colorEquity)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Strategy Table */}
              <div className="glass-panel table-section">
                <div className="table-header">
                  <h2>Operational Deployment Fleet</h2>
                  <div className="table-filters">
                    <select value={selectedStatus} onChange={(e) => setSelectedStatus(e.target.value)}>
                      <option value="all">ALL NODES</option>
                      <option value="paper">PAPER</option>
                      <option value="live">LIVE</option>
                      <option value="retired">RETIRED</option>
                    </select>
                  </div>
                </div>
                <table className="ultimate-table">
                  <thead>
                    <tr>
                      <th>Asset / Strategy</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Backtest Sharpe</th>
                      <th>Global PnL</th>
                      <th>Metrics</th>
                      <th style={{ textAlign: 'right' }}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {strategies.map(s => (
                      <tr key={s.id} className="row">
                        <td>
                          <div className="asset-cell">
                            <div className="info">
                              <span className="symbol">{s.symbol}</span>
                              <span className="name">{s.name.substring(0, 20)}...</span>
                            </div>
                          </div>
                        </td>
                        <td><span className="type-badge">{s.type}</span></td>
                        <td><span className={`status-pill ${s.status}`}>{s.status.toUpperCase()}</span></td>
                        <td className="numeric">{(s.bt_sharpe || 0).toFixed(2)}</td>
                        <td className={`numeric ${s.live_pnl >= 0 ? 'profit' : 'loss'}`}>
                          ${(s.live_pnl || 0).toFixed(2)}
                        </td>
                        <td>
                          <div className="mini-stats">
                            <span className="stat-pill">{s.live_trades || 0} execs</span>
                            <span className="stat-pill">{(s.live_drawdown || 0).toFixed(1)}% risk</span>
                          </div>
                        </td>
                        <td style={{ textAlign: 'right' }}>
                          <button className="retire-action" onClick={() => retireStrategy(s.id)}>DECOMMISSION</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="right-column">
              {/* Hot Symbols / Adrenaline Wave */}
              <div className="glass-panel side-panel adrenaline-panel">
                <h3>HOT_ADRENALINE_WAVE</h3>
                <div className="hot-symbols">
                  {hotSymbols.slice(0, 5).map(s => (
                    <div key={s.symbol} className="hot-item">
                      <div className="hot-header">
                        <span className="sym">{s.symbol}</span>
                        <span className="score">ADR: {s.adrenaline_score}</span>
                      </div>
                      <div className="hot-bar-bg">
                        <div className="hot-bar-fill" style={{ width: `${Math.min(s.adrenaline_score * 2.5, 100)}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Market Pulse Panel */}
              <div className="glass-panel side-panel">
                <h3>QUANT_RECON_FEED</h3>
                <div className="market-pulse">
                  {marketPulse.map(m => (
                    <div key={m.symbol} className="market-item">
                      <span className="sym">{m.symbol}</span>
                      <span className="price">{m.bid.toFixed(m.symbol.includes('JPY') ? 3 : 5)}</span>
                      <span className={`change ${m.change >= 0 ? 'up' : 'down'}`}>
                        {m.change >= 0 ? '+' : ''}{m.change}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Autonomous Operations Log */}
              <div className="glass-panel side-panel">
                <h3>INTEL_STREAM</h3>
                <div className="terminal" ref={terminalRef}>
                  {logs.map((l, i) => (
                    <div key={i} className="terminal-line">
                      <span className="t">[{l.time.split('T')[1]?.substring(0, 8) || ''}]</span>
                      <span className="src">{l.source.toUpperCase()}</span>
                      <span className="msg">{l.msg}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      <footer className="footer">
        <div className="footer-left">TITAN CONTROL SYSTEMS :: QUANT_FABRICATION_LAB :: NODE_{Math.random().toString(36).substring(7).toUpperCase()}</div>
        <div className="footer-right">BROKER: XMGLOBAL | REGIME: VOLATILE_TREND | UTC: {new Date().toISOString()}</div>
      </footer>
    </div>
  )
}

export default App
