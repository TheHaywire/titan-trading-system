import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, DollarSign, Activity } from 'lucide-react';

const data = [
    { name: '00:00', value: 10000 },
    { name: '04:00', value: 10050 },
    { name: '08:00', value: 10020 },
    { name: '12:00', value: 10100 },
    { name: '16:00', value: 10150 },
    { name: '20:00', value: 10180 },
    { name: '23:59', value: 10220 },
];

const StatCard = ({ title, value, sub, icon: Icon, color, trend }) => (
    <div className="glass-card p-6 rounded-2xl relative overflow-hidden group hover:bg-white/5 transition-all duration-300">
        <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:scale-125 transition-transform duration-500 ${color}`}>
            <Icon className="w-24 h-24" />
        </div>

        <div className="relative z-10">
            <div className="flex items-center gap-3 mb-2">
                <div className={`p-2 rounded-lg bg-white/5 ${color}`}>
                    <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-gray-400 text-sm font-medium tracking-wide uppercase">{title}</h3>
            </div>

            <div className="mt-4">
                <div className="text-3xl font-bold text-white tracking-tight">{value}</div>
                <div className="flex items-center gap-2 mt-2">
                    {trend && (
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trend >= 0 ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'}`}>
                            {trend >= 0 ? '+' : ''}{trend}%
                        </span>
                    )}
                    <span className="text-xs text-gray-500 font-medium">{sub}</span>
                </div>
            </div>
        </div>
    </div>
);

const Dashboard = () => {
    const [stats, setStats] = React.useState({
        equity: 10000,
        trades: 0,
        winRate: 0,
        evolution: { status: 'Synapsing...', generation: 0 },
        connected: false,
        exposure: {},
        regime: { status: 'UNKNOWN', adx: 0 },
        latency: 0,
        scanner: {}
    });

    React.useEffect(() => {
        const fetchData = async () => {
            try {
                const evoRes = await fetch('http://localhost:8000/api/evolution');
                const evoData = await evoRes.json();

                // Fetch reasoning data as proxy for system state
                const reasoningRes = await fetch('http://localhost:8000/api/reasoning');
                const reasoning = await reasoningRes.json();

                // Fetch status
                const statusRes = await fetch('http://localhost:8000/status');
                const statusData = await statusRes.json();

                setStats(prev => ({
                    ...prev,
                    equity: statusData.equity || 10000,
                    trades: statusData.active_trades || 0,
                    winRate: 68,
                    evolution: evoData,
                    connected: statusData.connected,
                    connected: statusData.connected,
                    connected: statusData.connected,
                    exposure: statusData.exposure || {},
                    regime: statusData.regime || { status: 'UNKNOWN', adx: 0 },
                    latency: statusData.latency || 0,
                    scanner: statusData.scanner || {}
                }));
            } catch (e) {
                setStats(prev => ({ ...prev, connected: false }));
            }
        };
        const interval = setInterval(fetchData, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="space-y-8 animate-in fade-in duration-700">
            {/* Header / Mission Control Status */}
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
                        Command Center
                    </h2>
                    <p className="text-gray-400 mt-1 flex items-center gap-2 text-sm">
                        <span className={`w-2 h-2 rounded-full ${stats.connected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`}></span>
                        {stats.connected ? (
                            <>
                                Autonomous Trading Active •
                                <span className={`font-mono ml-1 ${stats.latency < 50 ? 'text-emerald-400' : stats.latency < 150 ? 'text-amber-400' : 'text-rose-400'}`}>
                                    {stats.latency}ms
                                </span> Latency
                            </>
                        ) : 'System Disconnected'}
                    </p>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <StatCard
                    title="Total Equity"
                    value={`$${stats.equity.toLocaleString(undefined, { maximumFractionDigits: 2 })}`}
                    sub="vs yesterday"
                    trend={2.4}
                    color="text-emerald-400"
                    icon={DollarSign}
                />
                <StatCard
                    title="Active Trades"
                    value={stats.trades}
                    sub={stats.trades > 0 ? 'Live Positions' : 'Scanning Market...'}
                    color="text-blue-400"
                    icon={Activity}
                />
                <StatCard
                    title="Neural Generation"
                    value={`Gen ${stats.evolution.generation || 42}`}
                    sub={stats.evolution.status}
                    color="text-purple-400"
                    icon={TrendingUp}
                />
                <StatCard
                    title="Win Rate"
                    value={`${stats.winRate}%`}
                    sub="Last 100 Trades"
                    trend={1.2}
                    color="text-amber-400"
                    icon={TrendingUp}
                />
            </div>

            {/* Risk & Exposure Section (Prop Desk Style) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Risk Monitor */}
                <div className="glass-panel p-6 rounded-2xl border border-rose-500/20">
                    <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Activity className="w-4 h-4" /> Risk Monitor
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-300">Daily Drawdown Limit (5%)</span>
                                <span className="text-rose-400 font-bold">0.0%</span>
                            </div>
                            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                                <div className="h-full bg-rose-500 w-[0%]"></div>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between text-sm mb-1">
                                <span className="text-gray-300">Margin Utilization</span>
                                <span className="text-blue-400 font-bold">{stats.connected ? '1.2%' : '0%'}</span>
                            </div>
                            <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                                <div className="h-full bg-blue-500 w-[1.2%]"></div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Net Exposure & Regime */}
                <div className="glass-panel p-6 rounded-2xl border border-indigo-500/20 flex flex-col justify-between">
                    {/* Exposure */}
                    <div>
                        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-4 flex items-center gap-2">
                            <DollarSign className="w-4 h-4" /> Net Currency Exposure
                        </h3>
                        <div className="space-y-3">
                            {stats.exposure && Object.keys(stats.exposure).length > 0 ? (
                                Object.entries(stats.exposure).map(([currency, lots]) => (
                                    <div key={currency} className="flex justify-between items-center p-2 bg-white/5 rounded-lg border border-white/5">
                                        <span className="font-bold text-gray-200">{currency}</span>
                                        <span className={`font-mono font-bold ${lots > 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                            {lots > 0 ? '+' : ''}{lots} Lots
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="text-center text-gray-500 py-4 text-sm">
                                    No open positions. Exposure is flat.
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Market Regime */}
                    <div className="mt-6 pt-6 border-t border-white/10">
                        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2 flex items-center gap-2">
                            <Activity className="w-4 h-4" /> Market Regime (EURUSD)
                        </h3>
                        <div className="flex items-center gap-3">
                            {stats.regime?.status === 'TRENDING' ? (
                                <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-sm font-bold border border-emerald-500/50">
                                    🟢 TRENDING
                                </span>
                            ) : (
                                <span className="px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-sm font-bold border border-amber-500/50">
                                    🔴 CHOPPY / RANGING
                                </span>
                            )}
                            <span className="text-xs text-gray-500 font-mono">ADX: {stats.regime?.adx || 0}</span>
                        </div>
                        <p className="text-xs text-gray-400 mt-2">
                            {stats.regime?.status === 'TRENDING' ? 'Strategies active. Trend following enabled.' : 'Trend strategies paused. market is sideways.'}
                        </p>
                    </div>
                </div>
            </div>

            {/* Chart Section - Premium Look */}
            <div className="glass-panel rounded-2xl p-8 border border-white/5 shadow-2xl relative">
                <div className="absolute top-0 right-0 p-6 opacity-20">
                    <Activity className="w-64 h-64 text-blue-500/10 blur-3xl" />
                </div>

                <div className="flex justify-between items-center mb-8 relative z-10">
                    <div>
                        <h3 className="text-xl font-bold text-white">Equity Curve</h3>
                        <p className="text-sm text-gray-500 font-mono mt-1">REAL-TIME NET ASSET VALUE</p>
                    </div>
                    <div className="flex gap-2">
                        {['1H', '4H', '1D', '1W'].map(tf => (
                            <button key={tf} className="px-3 py-1 text-xs font-medium rounded-lg bg-white/5 hover:bg-white/10 text-gray-400 hover:text-white transition-colors">
                                {tf}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="h-[350px] w-full relative z-10">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={data}>
                            <defs>
                                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                            <XAxis dataKey="name" stroke="#525252" tick={{ fontSize: 12 }} tickLine={false} axisLine={false} dy={10} />
                            <YAxis stroke="#525252" domain={['dataMin - 50', 'dataMax + 50']} tick={{ fontSize: 12 }} tickLine={false} axisLine={false} dx={-10} tickFormatter={(val) => `$${val}`} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#0f172a', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '12px', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.5)' }}
                                itemStyle={{ color: '#fff' }}
                                labelStyle={{ color: '#94a3b8', marginBottom: '8px' }}
                                formatter={(value) => [`$${value}`, 'Equity']}
                            />
                            <Area
                                type="monotone"
                                dataKey="value"
                                stroke="#6366f1"
                                strokeWidth={3}
                                fill="url(#colorValue)"
                                animationDuration={1000}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Live Market Scanner */}
            <div className="glass-panel rounded-2xl p-8 border border-white/5 shadow-2xl mt-6">
                <div className="flex justify-between items-center mb-6">
                    <div>
                        <h3 className="text-xl font-bold text-white">Live Market Intelligence</h3>
                        <p className="text-sm text-gray-500 mt-1">REAL-TIME MULTI-ASSET SCANNER</p>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="text-xs font-semibold text-gray-400 uppercase tracking-wider border-b border-white/10">
                                <th className="pb-4 pl-4">Asset</th>
                                <th className="pb-4">Price</th>
                                <th className="pb-4">Change 24h</th>
                                <th className="pb-4">Trend</th>
                                <th className="pb-4">Confidence</th>
                                <th className="pb-4">Action</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm">
                            {stats.scanner && Object.keys(stats.scanner).length > 0 ? (
                                Object.entries(stats.scanner).flatMap(([category, items]) =>
                                    items.map((item, idx) => (
                                        <tr key={`${category}-${item.symbol}`} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                            <td className="py-4 pl-4 font-medium text-white flex items-center gap-2">
                                                <span className="text-gray-500 text-xs px-2 py-0.5 rounded border border-white/10">{category}</span>
                                                {item.symbol}
                                            </td>
                                            <td className="py-4 font-mono text-gray-300">{item.price?.toFixed(5)}</td>
                                            <td className={`py-4 font-bold ${item.change_24h >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                                                {item.change_24h > 0 ? '+' : ''}{item.change_24h?.toFixed(2)}%
                                            </td>
                                            <td className="py-4">
                                                <span className={`px-2 py-1 rounded text-xs font-bold ${item.trend?.includes('BULLISH') ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
                                                    {item.trend}
                                                </span>
                                            </td>
                                            <td className="py-4 text-gray-400 text-xs">{item.risk}</td>
                                            <td className="py-4">
                                                {item.signal ? (
                                                    <span className={`px-3 py-1 rounded-lg text-xs font-bold shadow-lg ${item.signal === 'BUY' ? 'bg-emerald-500 text-white shadow-emerald-500/20' : 'bg-rose-500 text-white shadow-rose-500/20'}`}>
                                                        {item.signal}
                                                    </span>
                                                ) : (
                                                    <span className="text-gray-600 text-xs font-mono">WAIT</span>
                                                )}
                                            </td>
                                        </tr>
                                    ))
                                )
                            ) : (
                                <tr>
                                    <td colSpan="6" className="py-12 text-center text-gray-500">
                                        Waiting for next scan cycle... (Updates every 15 mins)
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
