import React, { useState, useEffect } from 'react';
import { Terminal, Cpu } from 'lucide-react';

const ReasoningConsole = () => {
    const [logs, setLogs] = useState([]);

    useEffect(() => {
        const fetchReasoning = async () => {
            try {
                const res = await fetch('http://localhost:8000/api/reasoning');
                const data = await res.json();
                const newLogs = [
                    ...data.accepted.map(l => ({ ...l, type: 'ACCEPTED', time: new Date().toLocaleTimeString() })),
                    ...data.rejected.map(l => ({ ...l, type: 'REJECTED', time: new Date().toLocaleTimeString() }))
                ]; // Time hack for demo since backend might not send it yet
                setLogs(newLogs);
            } catch (error) {
                // silent
            }
        };
        const interval = setInterval(fetchReasoning, 2000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="glass-panel p-6 rounded-2xl h-[400px] flex flex-col font-mono text-xs md:text-sm border border-white/5 relative overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-4 z-10">
                <div className="flex items-center gap-2 text-indigo-400">
                    <Terminal className="w-4 h-4" />
                    <span className="font-bold tracking-wider uppercase">Neurological Output</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                    <span className="text-gray-500 text-xs">LIVE STREAMING</span>
                </div>
            </div>

            {/* Matrix Background Effect */}
            <div className="absolute inset-0 bg-blue-500/5 blur-3xl rounded-full opacity-10 pointer-events-none" />

            {/* Content */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-indigo-500/20 scrollbar-track-transparent z-10">
                {logs.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-600 gap-2">
                        <Cpu className="w-8 h-8 opacity-20 animate-spin-slow" />
                        <span className="opacity-50">Awaiting Neural Signals...</span>
                    </div>
                ) : (
                    logs.map((log, idx) => (
                        <div key={idx} className={`p-3 rounded-lg border flex flex-col gap-1 transition-all duration-300 hover:translate-x-1 ${log.type === 'ACCEPTED'
                                ? 'bg-emerald-500/5 border-emerald-500/10 hover:border-emerald-500/30'
                                : 'bg-rose-500/5 border-rose-500/10 hover:border-rose-500/30'
                            }`}>
                            <div className="flex justify-between items-center opacity-70">
                                <span className="text-gray-400">[{log.time || 'now'}]</span>
                                <span className={`font-bold text-xs px-2 py-0.5 rounded ${log.type === 'ACCEPTED' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                                    }`}>{log.type}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-gray-200 font-bold text-base">{log.symbol}</span>
                                <span className="text-gray-600">to</span>
                                <span className="text-indigo-300">
                                    {log.data ? `${log.data.trend} TREND` : log.reason_code}
                                </span>
                            </div>
                            <p className="text-gray-400 border-l-2 border-white/10 pl-2 mt-1 italic">
                                "{log.why || log.reason_text || log.reason || "Analyzing patterns..."}"
                            </p>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default ReasoningConsole;
