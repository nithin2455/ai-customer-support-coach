import React from 'react';
import { Flame, AlertTriangle } from 'lucide-react';

export default function StressGauge({ score = 0 }) {
  let barColor = 'bg-emerald-600';
  let badgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let levelText = 'Low';

  if (score >= 81) {
    barColor = 'bg-rose-600';
    badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
    levelText = 'Critical';
  } else if (score >= 61) {
    barColor = 'bg-amber-600';
    badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
    levelText = 'High';
  } else if (score >= 31) {
    barColor = 'bg-amber-500';
    badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
    levelText = 'Moderate';
  }

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Flame className={`w-3.5 h-3.5 ${score >= 61 ? 'text-rose-600' : 'text-amber-500'}`} />
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-700">Customer Stress Score</span>
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border ${badgeClass}`}>
          {score}/100 • {levelText}
        </span>
      </div>

      {/* Progress Bar Gauge */}
      <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full ${barColor} transition-all duration-300`}
          style={{ width: `${Math.min(Math.max(score, 4), 100)}%` }}
        />
      </div>

      <div className="flex justify-between text-[10px] text-slate-400 font-sans">
        <span>0 Low</span>
        <span>31 Moderate</span>
        <span>61 High</span>
        <span>81 Critical</span>
      </div>
    </div>
  );
}
