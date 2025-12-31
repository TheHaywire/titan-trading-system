import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

const LogViewer = () => {
    const [logs, setLogs] = useState([]);
    const ws = useRef(null);
    const bottomRef = useRef(null);

    useEffect(() => {
        // Connect WS
        ws.current = new WebSocket('ws://localhost:8000/ws/logs');

        ws.current.onmessage = (event) => {
            setLogs(prev => [...prev.slice(-100), event.data]); // Keep last 100
        };

        return () => {
            if (ws.current) ws.current.close();
        };
    }, []);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <div className="bg-dark-800 border border-dark-700 rounded-xl overflow-hidden shadow-xl flex flex-col h-[400px]">
            <div className="px-6 py-4 border-b border-dark-700 bg-dark-800 flex items-center gap-2">
                <Terminal className="w-4 h-4 text-gray-400" />
                <h3 className="text-sm font-semibold text-gray-200">System Logs</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4 bg-dark-950 font-mono text-xs text-gray-400 space-y-1">
                {logs.length === 0 && (
                    <div className="text-center py-10 opacity-30">Waiting for logs...</div>
                )}
                {logs.map((log, i) => (
                    <div key={i} className="hover:bg-white/5 px-2 py-0.5 rounded transition-colors whitespace-pre-wrap break-words border-l-2 border-transparent hover:border-primary/50">
                        {log}
                    </div>
                ))}
                <div ref={bottomRef} />
            </div>
        </div>
    );
};

export default LogViewer;
