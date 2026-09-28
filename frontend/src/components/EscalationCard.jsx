import React from 'react';
import { ShieldAlert, AlertOctagon, CheckCircle2, ChevronRight } from 'lucide-react';

export default function EscalationCard({ escalation }) {
  if (!escalation || !escalation.escalation_recommended) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 text-xs flex items-center justify-between text-slate-600">
        <span className="flex items-center gap-1.5 font-medium">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
          Standard Handling
        </span>
        <span className="text-[10px] text-slate-400">No Escalation Needed</span>
      </div>
    );
  }

  const isCritical = escalation.escalation_tier === 'CRITICAL';
  const cardBg = isCritical
    ? 'bg-rose-50 border-rose-200 text-rose-900'
    : 'bg-amber-50 border-amber-200 text-amber-900';

  const badgeBg = isCritical
    ? 'bg-rose-100 text-rose-800 border-rose-300'
    : 'bg-amber-100 text-amber-800 border-amber-300';

  return (
    <div className={`border rounded-lg p-3 space-y-2 ${cardBg}`}>
      <div className="flex items-center justify-between border-b border-rose-100 pb-1.5">
        <div className="flex items-center space-x-1.5">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <span className="text-xs font-bold uppercase tracking-wider">Escalation Alert</span>
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded border uppercase ${badgeBg}`}>
          {escalation.escalation_tier} Escalation
        </span>
      </div>

      <div className="space-y-1 text-xs">
        <span className="text-[10px] text-slate-500 block font-semibold uppercase">Escalation Rationale</span>
        <div className="space-y-0.5">
          {(escalation.reasons_list || []).map((reason, idx) => (
            <div key={idx} className="flex items-start space-x-1.5 text-[11px] text-slate-800">
              <span className="text-rose-600 font-bold">•</span>
              <span>{reason}</span>
            </div>
          ))}
        </div>
      </div>

      {escalation.recommended_action && (
        <div className="bg-white p-2.5 rounded border border-rose-200 text-[11px]">
          <span className="font-semibold block text-[10px] text-indigo-700 uppercase mb-0.5">Recommended Action</span>
          <p className="text-slate-700 leading-snug">{escalation.recommended_action}</p>
        </div>
      )}
    </div>
  );
}
