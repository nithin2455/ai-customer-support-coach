import React from 'react';
import { History, UserCheck, Compass, AlertCircle, Award } from 'lucide-react';

export default function CustomerMemoryCard({ customer }) {
  if (!customer) return null;

  const badge = customer.badge || (customer.total_contacts > 2 ? 'Repeated Issue Customer' : 'Returning Customer');

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2.5">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center space-x-1.5">
          <History className="w-3.5 h-3.5 text-indigo-600" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">Customer Profile & Context</h3>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded border ${
          badge === 'Repeated Issue Customer'
            ? 'bg-rose-50 text-rose-700 border-rose-200'
            : 'bg-indigo-50 text-indigo-700 border-indigo-200'
        }`}>
          {badge}
        </span>
      </div>

      {/* Profile Overview Grid */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-slate-400 text-[10px] block">Customer Name</span>
          <span className="font-semibold text-slate-800">{customer.name} ({customer.tier})</span>
        </div>
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-slate-400 text-[10px] block">Total Touchpoints</span>
          <span className="font-semibold text-slate-800">{customer.total_contacts} Interactions</span>
        </div>
      </div>

      {/* Style & History Card */}
      <div className="bg-white p-2.5 rounded border border-slate-200 text-xs space-y-1">
        <div className="flex items-center justify-between text-indigo-700 font-medium">
          <span className="flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-indigo-600" /> Communication Style
          </span>
          <span className="text-slate-800 font-semibold">{customer.predicted_style}</span>
        </div>
      </div>

      {/* Historical Touchpoint Notes */}
      {customer.memories && customer.memories.length > 0 && (
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Previous Touchpoint Memory:</span>
          {customer.memories.slice(0, 2).map((mem, idx) => (
            <div key={mem.id || idx} className="bg-white p-2 rounded border border-slate-200 text-xs space-y-1">
              <div className="flex items-center justify-between text-[10px] text-slate-400">
                <span>Agent: <strong className="text-slate-700">{mem.agent_name || 'Sarah Jenkins'}</strong></span>
                <span className="text-rose-600 font-medium">{mem.sentiment_label || 'Negative'}</span>
              </div>
              <p className="text-slate-700 font-medium text-[11px]">{mem.issue_summary}</p>
              {mem.resolution_summary && (
                <p className="text-emerald-700 text-[11px]">Res: {mem.resolution_summary}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
