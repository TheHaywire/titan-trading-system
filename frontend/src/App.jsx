
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Activity, Shield, Zap, TrendingUp, Power } from 'lucide-react';
import MarketCard from './components/MarketCard';
import StatusBadge from './components/StatusBadge';
import { motion } from 'framer-motion';

const API_URL = 'http://localhost:8000';

function App() {
    const [status, setStatus] = useState(null);
    const [analysis, setAnalysis] = useState([]);
    const [logs, setLogs] = useState([]);
    const [connected, setConnected] = useState(false);

    // Poll for data every 2 seconds
    useEffect(() => {
        const fetchData = async () => {
            try {
                const [statusRes, reasoningRes] = await Promise.all([
                    axios.get(`${API_URL}/status`),
                    axios.get(`${API_URL}/api/reasoning`)
                ]);

                setStatus(statusRes.data);
                setAnalysis(reasoningRes.data.analysis);
                setConnected(true);
            } catch (err) {
                setConnected(false);
                console.error("Connection Error", err);
            }
        };

        const interval = setInterval(fetchData, 2000);
        fetchData();
        return () => clearInterval(interval);
    }, []);

    const toggleEngine = async () => {
        if (status?.running) {
            await axios.post(`${API_URL}/stop`);
        } else {
            await axios.post(`${API_URL}/start`);
        }
    };

    return (
        <div className="min-h-screen bg-titan-dark text-gray-100 p-6">
            {/* Header */}
            <header className="max-w-7xl mx-auto flex justify-between items-center mb-10">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
                        TITAN INTELLIGENCE
                    </h1>
                    <p className="text-gray-400 text-sm flex items-center gap-2 mt-1">
                        <span className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></span>
                        {connected ? "System Online" : "Disconnected"}
                    </p>
                </div>

                <div className="flex gap-4">
                    <button
                        onClick={toggleEngine}
                        className={`flex items-center gap-2 px-6 py-2 rounded-lg font-medium transition-all ${status?.running
                                ? 'bg-red-500/10 text-red-400 border border-red-500/50 hover:bg-red-500/20'
                                : 'bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/20'
                            }`}
                    >
                        <Power size={18} />
                        {status?.running ? "STOP ENGINE" : "ACTIVATE TITAN"}
                    </button>
                </div>
            </header>

            <main className="max-w-7xl mx-auto grid grid-cols-12 gap-8">

                {/* Left Col: KPI Cards */}
                <div className="col-span-12 grid grid-cols-1 md:grid-cols-4 gap-4">
                    <StatsCard
                        icon={<Shield size={24} className="text-blue-400" />}
                        label="Total Equity"
                        value={`$${status?.equity?.toFixed(2) || '0.00'}`}
                    />
                    <StatsCard
                        icon={<Zap size={24} className="text-yellow-400" />}
                        label="Active Trades"
                        value={status?.active_trades || 0}
                    />
                    <StatsCard
                        icon={<Activity size={24} className="text-purple-400" />}
                        label="Market Scanned"
                        value={analysis.length || 0}
                    />
                    <StatusBadge running={status?.running} />
                </div>

                {/* Main Content: Signal Cards */}
                <div className="col-span-12 lg:col-span-8">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-xl font-semibold flex items-center gap-2">
                            <TrendingUp size={20} className="text-emerald-400" />
                            Market Opportunities
                        </h2>
                        <span className="text-xs text-gray-500 bg-white/5 px-2 py-1 rounded">Live Analysis</span>
                    </div>

                    <div className="grid grid-cols-1 gap-4">
                        {analysis.map((item) => (
                            <MarketCard key={item.symbol} data={item} />
                        ))}
                        {analysis.length === 0 && (
                            <div className="glass-panel p-10 text-center text-gray-500">
                                Waiting for market scan data...
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Sidebar: Logs or Details */}
                <div className="col-span-12 lg:col-span-4 space-y-4">
                    <div className="glass-panel p-6 h-full min-h-[400px]">
                        <h3 className="text-lg font-semibold mb-4 text-gray-300">System Logs</h3>
                        <div className="space-y-2 text-xs font-mono text-gray-400 h-[350px] overflow-y-auto">
                            {/* Placeholder for logs WebSocket integration */}
                            <p>[INFO] Titan Engine initialized</p>
                            <p>[INFO] Connecting to MT5...</p>
                            <p>[INFO] Data feed active.</p>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}

function StatsCard({ icon, label, value }) {
    return (
        <div className="glass-panel p-4 flex items-center gap-4">
            <div className="p-3 bg-white/5 rounded-lg">{icon}</div>
            <div>
                <p className="text-gray-400 text-xs uppercase tracking-wider">{label}</p>
                <p className="text-xl font-bold text-white">{value}</p>
            </div>
        </div>
    );
}

export default App;
