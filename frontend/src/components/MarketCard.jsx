
import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

const MarketCard = ({ data }) => {
    // Determine status color based on Score
    const getScoreColor = (score) => {
        if (score >= 70) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10';
        if (score <= 30) return 'text-red-400 border-red-500/30 bg-red-500/10';
        return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
    };

    const isBuy = data.signal === 'BUY';
    const isSell = data.signal === 'SELL';

    return (
        <div className="glass-card p-5 flex flex-col md:flex-row gap-6 hover:border-blue-500/30 group">

            {/* Left: Symbol & Price */}
            <div className="flex-shrink-0 w-32">
                <h3 className="text-2xl font-bold tracking-tight text-white">{data.symbol}</h3>
                <p className="text-sm font-mono text-gray-400 mt-1">${data.price?.toFixed(5)}</p>
                <div className={`mt-2 inline-flex items-center gap-1 text-xs px-2 py-1 rounded border ${data.change_24h >= 0 ? 'text-emerald-400 border-emerald-500/20 bg-emerald-500/5' : 'text-red-400 border-red-500/20 bg-red-500/5'
                    }`}>
                    {data.change_24h >= 0 ? '+' : ''}{data.change_24h?.toFixed(2)}%
                </div>
            </div>

            {/* Middle: Score & Strategy Categories */}
            <div className="flex-[2] flex flex-col md:flex-row items-center border-l border-r border-white/5 px-6 gap-6">
                <div className="text-center min-w-[80px]">
                    <div className="text-xs text-gray-500 uppercase tracking-widest mb-1">Titan Score</div>
                    <div className={`text-4xl font-black ${data.score > 60 ? 'text-emerald-400 shadow-emerald-500/20' :
                        data.score < 40 ? 'text-red-400 shadow-red-500/20' : 'text-gray-400'
                        } drop-shadow-lg`}>
                        {data.score}
                    </div>
                </div>

                {/* Live Strategy Categories */}
                <div className="grid grid-cols-2 gap-3 w-full">
                    {data.categories && Object.entries(data.categories).map(([name, info]) => (
                        <div key={name} className="bg-white/5 rounded-lg p-2 border border-white/5">
                            <div className="text-[10px] text-gray-400 uppercase tracking-tight">{name}</div>
                            <div className="flex items-center gap-2 mt-1">
                                <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className={`h-full rounded-full ${info.score > 70 ? 'bg-emerald-500' : info.score > 40 ? 'bg-yellow-500' : 'bg-red-500'}`}
                                        style={{ width: `${info.score || 50}%` }}
                                    />
                                </div>
                                <span className={`text-[10px] font-bold ${info.score > 70 ? 'text-emerald-400' : 'text-gray-300'}`}>
                                    {info.label}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Right: Reasoning & Action */}
            <div className="flex-1 min-w-[200px] flex flex-col justify-between">
                <div className="space-y-2">
                    <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-gray-500 uppercase">Reasoning</span>
                        {data.risk === 'HIGH' && (
                            <span className="text-[10px] bg-red-500 text-white px-1.5 py-0.5 rounded flex items-center gap-1">
                                <AlertTriangle size={10} /> High Risk
                            </span>
                        )}
                    </div>

                    {data.reasoning && data.reasoning.slice(0, 2).map((reason, idx) => (
                        <div key={idx} className="flex items-start gap-2 text-sm text-gray-300">
                            <CheckCircle size={14} className="mt-0.5 text-blue-500" />
                            <span>{reason}</span>
                        </div>
                    ))}

                    {/* AI Insight Block */}
                    {/* AI Insight Block (JSON Parsed) */}
                    {data.ai_insight && (
                        (() => {
                            try {
                                const aiData = typeof data.ai_insight === 'string' ? JSON.parse(data.ai_insight) : data.ai_insight;
                                if (!aiData.summary) return null;

                                return (
                                    <div className="mt-3 p-3 rounded bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20">
                                        <div className="flex items-center justify-between mb-2">
                                            <div className="flex items-center gap-1 text-[10px] uppercase text-blue-400 font-bold">
                                                <span>✨ Titan AI</span>
                                            </div>
                                            {aiData.confidence && (
                                                <span className="text-[10px] text-gray-400">Conf: {aiData.confidence}%</span>
                                            )}
                                        </div>
                                        <p className="text-xs text-blue-100 italic mb-2">"{aiData.summary}"</p>

                                        {/* Trade Setup Mini-View */}
                                        {aiData.trade_setup && (
                                            <div className="grid grid-cols-2 gap-1 text-[10px] mt-1 border-t border-white/5 pt-1">
                                                <div className="text-gray-400">Entry: <span className="text-white">{aiData.trade_setup.entry_zone}</span></div>
                                                <div className="text-gray-400 text-right">TP1: <span className="text-emerald-400">{aiData.trade_setup.take_profit_1}</span></div>
                                                <div className="text-gray-400">SL: <span className="text-red-400">{aiData.trade_setup.stop_loss}</span></div>
                                                <div className="text-gray-400 text-right">Bias: <span className={aiData.bias === 'BULLISH' ? 'text-emerald-400' : 'text-red-400'}>{aiData.bias}</span></div>
                                            </div>
                                        )}
                                    </div>
                                );
                            } catch (e) {
                                return (
                                    <div className="mt-3 p-2 text-xs text-gray-500 italic">
                                        Analyzing market structure...
                                    </div>
                                );
                            }
                        })()
                    )}
                </div>

                {/* Signal Button */}
                <div className="mt-4 flex justify-end">
                    {isBuy && (
                        <button className="flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white px-4 py-2 rounded-lg font-bold shadow-lg shadow-emerald-500/20 transition-all">
                            BUY SIGNAL <ArrowUpRight size={18} />
                        </button>
                    )}
                    {isSell && (
                        <button className="flex items-center gap-2 bg-red-500 hover:bg-red-400 text-white px-4 py-2 rounded-lg font-bold shadow-lg shadow-red-500/20 transition-all">
                            SELL SIGNAL <ArrowDownRight size={18} />
                        </button>
                    )}
                    {!isBuy && !isSell && (
                        <div className="text-gray-600 text-sm font-medium flex items-center gap-2">
                            <Activity size={16} /> Monitoring
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default MarketCard;
