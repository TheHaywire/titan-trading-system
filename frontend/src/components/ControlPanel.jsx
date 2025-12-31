import React, { useState, useEffect } from 'react';
import { Play, Square, Settings, RefreshCw } from 'lucide-react';
import { startBot, stopBot, getStatus } from '../api';

const ControlPanel = () => {
    const [status, setStatus] = useState({ running: false, connected: false, symbols: 0 });
    const [loading, setLoading] = useState(false);

    const fetchStatus = async () => {
        try {
            const res = await getStatus();
            setStatus(res.data);
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleStart = async () => {
        setLoading(true);
        await startBot();
        await fetchStatus();
        setLoading(false);
    };

    const handleStop = async () => {
        setLoading(true);
        await stopBot();
        await fetchStatus();
        setLoading(false);
    };

    return (
        <div className="bg-dark-800 border border-dark-700 rounded-xl p-6 shadow-xl h-full flex flex-col justify-between">
            <div>
                <h2 className="text-lg font-semibold mb-4 text-gray-100 flex items-center gap-2">
                    <Settings className="w-5 h-5 text-gray-400" />
                    Controls
                </h2>

                <div className="space-y-4 mb-6">
                    <div className="flex justify-between items-center p-3 bg-dark-900/50 rounded-lg border border-dark-700">
                        <span className="text-gray-400 text-sm">MT5 Connection</span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${status.connected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'}`}>
                            {status.connected ? 'Connected' : 'Disconnected'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-dark-900/50 rounded-lg border border-dark-700">
                        <span className="text-gray-400 text-sm">Active Symbols</span>
                        <span className="text-gray-100 font-mono text-sm">{status.symbols}</span>
                    </div>
                </div>
            </div>

            <div className="space-y-3">
                {!status.running ? (
                    <button
                        onClick={handleStart}
                        disabled={loading}
                        className="w-full py-3 bg-primary hover:bg-primary-hover text-white rounded-lg font-medium transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        <Play className="w-5 h-5 fill-current" />
                        Start Trading
                    </button>
                ) : (
                    <button
                        onClick={handleStop}
                        disabled={loading}
                        className="w-full py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-all shadow-lg shadow-red-500/20 flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                        <Square className="w-5 h-5 fill-current" />
                        Stop Bot
                    </button>
                )}
            </div>
        </div>
    );
};

export default ControlPanel;
