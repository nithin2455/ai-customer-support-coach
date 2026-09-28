import React from 'react';
import { Calendar, CheckCircle, Clock, UserCheck, Flame } from 'lucide-react';

export default function CustomerTimeline({ timeline = [] }) {
  if (!timeline || timeline.length === 0) return null;

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2.5">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center space-x-1.5">
          <Calendar className="w-3.5 h-3.5 text-indigo-600" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">Interaction Timeline</h3>
        </div>
        <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">
          {timeline.length} Events
        </span>
      </div>

      <div className="relative border-l border-slate-200 ml-2 pl-3.5 space-y-2.5 my-1">
        {timeline.map((item, idx) => (
          <div key={idx} className="relative">
            {/* Dot Indicator */}
            <span className={`absolute -left-[19px] top-1.5 w-2 h-2 rounded-full ${
              item.status === 'Resolved' ? 'bg-emerald-500' : 'bg-rose-500'
            }`} />

            <div className="bg-white p-2.5 rounded border border-slate-200 space-y-1 text-xs">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-semibold text-slate-800">{item.step} • {item.date}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded border font-medium ${
                  item.stress_score >= 70 ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                }`}>
                  Stress: {item.stress_score}
                </span>
              </div>

              <p className="text-slate-600 text-[11px] leading-snug">{item.issue}</p>

              <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1 border-t border-slate-100">
                <span>Agent: <strong className="text-slate-700">{item.agent}</strong></span>
                <span className="text-indigo-600 truncate max-w-[150px]">Res: {item.resolution}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
