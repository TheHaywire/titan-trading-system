
import React from 'react';

const StatusBadge = ({ running }) => {
    return (
        <div className="glass-panel p-4 flex flex-col items-center justify-center relative overflow-hidden">
            <div className={`absolute inset-0 opacity-10 ${running ? 'bg-emerald-500' : 'bg-red-500'}`}></div>

            <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">System State</div>
            <div className={`text-lg font-bold flex items-center gap-2 ${running ? 'text-emerald-400' : 'text-red-400'}`}>
                {running ? "ACTIVE" : "STANDBY"}
                <span className={`relative flex h-3 w-3`}>
                    {running && <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>}
                    <span className={`relative inline-flex rounded-full h-3 w-3 ${running ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                </span>
            </div>
        </div>
    );
};

export default StatusBadge;
