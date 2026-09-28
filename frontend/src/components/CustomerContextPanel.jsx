import React, { useState } from 'react';
import { User, ShieldAlert, Clock, AlertTriangle, CheckCircle2, RotateCcw, Compass, ArrowRightLeft, History, ChevronDown, ChevronUp } from 'lucide-react';
import AgentContinuityCard from './AgentContinuityCard';
import CustomerTimeline from './CustomerTimeline';

export default function CustomerContextPanel({
  customer,
  slaInfo,
  escalationInfo,
  repeatedIssue,
  continuity,
  timeline = [],
  onTransfer
}) {
  const [showTimeline, setShowTimeline] = useState(false);
  const [showTransfer, setShowTransfer] = useState(false);

  if (!customer) {
    return (
      <div className="p-4 text-xs text-slate-400 text-center">
        No customer selected
      </div>
    );
  }

  const stressScore = customer.current_stress_score || 0;
  const isVip = customer.tier === 'VIP';
  const isRepeated = repeatedIssue?.is_repeated_issue;
  const isEscalationRec = escalationInfo?.escalation_recommended;
  const slaStatus = slaInfo?.status || 'On Track';

  // Stress bar color
  const stressColor = stressScore >= 70
    ? 'bg-rose-500'
    : stressScore >= 40
      ? 'bg-amber-500'
      : 'bg-emerald-500';

  // SLA badge color
  const slaBadgeClass = slaStatus.includes('Breached')
    ? 'bg-rose-50 text-rose-700 border-rose-200'
    : slaStatus === 'At Risk'
      ? 'bg-amber-50 text-amber-700 border-amber-200'
      : 'bg-emerald-50 text-emerald-700 border-emerald-200';

  return (
    <div className="w-80 bg-white border-l border-slate-200 flex flex-col h-full overflow-y-auto shrink-0 divide-y divide-slate-100 text-slate-800">
      {/* Panel Title */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <User className="w-4 h-4 text-indigo-600" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Customer Context</h3>
        </div>
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
          isVip ? 'bg-purple-50 text-purple-700 border-purple-200' : 'bg-slate-100 text-slate-600 border-slate-200'
        }`}>
          {customer.tier || 'Standard'}
        </span>
      </div>

      {/* Customer Info */}
      <div className="p-4 space-y-2 text-xs">
        <div className="flex items-start justify-between">
          <div>
            <h4 className="font-bold text-sm text-slate-900">{customer.name}</h4>
            <p className="text-slate-500 text-[11px]">{customer.email}</p>
            {customer.phone && <p className="text-slate-400 text-[11px]">{customer.phone}</p>}
          </div>
          <span className="text-[10px] text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded font-medium">
            {customer.badge || 'Returning'}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-1 text-[11px]">
          <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
            <span className="text-slate-400 text-[10px] block">Interactions</span>
            <span className="font-bold text-slate-800">{customer.total_contacts || 1} contacts</span>
          </div>
          <div className="bg-slate-50 p-2 rounded-lg border border-slate-200/60">
            <span className="text-slate-400 text-[10px] block">Unresolved</span>
            <span className={`font-bold ${customer.unresolved_issues > 0 ? 'text-amber-600' : 'text-slate-700'}`}>
              {customer.unresolved_issues || 0} issues
            </span>
          </div>
        </div>
      </div>

      {/* Previous Issue Summary (from memory) */}
      <div className="p-4 space-y-1.5 text-xs">
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">Previous Issue</span>
        {customer.memories && customer.memories.length > 0 ? (
          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80 text-[11px] space-y-1">
            <div className="flex items-center justify-between text-slate-400 text-[10px]">
              <span>Agent: {customer.memories[0].agent_name || 'Sarah Jenkins'}</span>
              <span className="text-rose-600 font-medium">{customer.memories[0].sentiment_label}</span>
            </div>
            <p className="text-slate-700 font-medium">{customer.memories[0].issue_summary}</p>
            {customer.memories[0].resolution_summary && (
              <p className="text-slate-500 text-[10px]">Res: {customer.memories[0].resolution_summary}</p>
            )}
          </div>
        ) : (
          <p className="text-slate-400 text-[11px] italic">No prior issue recorded</p>
        )}
      </div>

      {/* Communication Style & Stress Gauge */}
      <div className="p-4 space-y-3 text-xs">
        <div className="flex items-center justify-between">
          <span className="text-slate-500 text-[11px] flex items-center gap-1">
            <Compass className="w-3.5 h-3.5 text-indigo-500" /> Style:
          </span>
          <span className="font-semibold text-slate-800 text-[11px] bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
            {customer.predicted_style || 'Direct'}
          </span>
        </div>

        <div className="space-y-1">
          <div className="flex justify-between items-center text-[11px]">
            <span className="text-slate-500">Stress Score:</span>
            <span className={`font-bold ${
              stressScore >= 70 ? 'text-rose-600' : stressScore >= 40 ? 'text-amber-600' : 'text-emerald-600'
            }`}>
              {stressScore} / 100
            </span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div
              className={`h-full ${stressColor} transition-all duration-300 rounded-full`}
              style={{ width: `${Math.min(stressScore, 100)}%` }}
            />
          </div>
        </div>
      </div>

      {/* Operational Indicators: Repeated Issue, SLA, Escalation */}
      <div className="p-4 space-y-2 text-xs">
        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">Workflow Indicators</span>

        {/* Repeated Issue */}
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/60">
          <div className="flex items-center space-x-1.5 text-[11px]">
            <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600">Repeated Issue:</span>
          </div>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
            isRepeated
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
          }`}>
            {isRepeated ? 'YES' : 'NO'}
          </span>
        </div>

        {/* Dynamic SLA */}
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/60">
          <div className="flex items-center space-x-1.5 text-[11px]">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600">SLA:</span>
          </div>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${slaBadgeClass}`}>
            {slaStatus}
          </span>
        </div>

        {/* Escalation */}
        <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-200/60">
          <div className="flex items-center space-x-1.5 text-[11px]">
            <ShieldAlert className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-slate-600">Escalation:</span>
          </div>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
            isEscalationRec
              ? 'bg-rose-50 text-rose-700 border-rose-200 font-semibold'
              : 'bg-slate-100 text-slate-600 border-slate-200'
          }`}>
            {isEscalationRec ? 'Recommended' : 'Standard'}
          </span>
        </div>
      </div>

      {/* Auxiliary Actions (Timeline & Transfer toggle) */}
      <div className="p-4 space-y-2">
        <button
          onClick={() => setShowTimeline(!showTimeline)}
          className="w-full py-1.5 px-2.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-between transition"
        >
          <span className="flex items-center gap-1.5 font-medium">
            <History className="w-3.5 h-3.5 text-indigo-500" />
            Touchpoint Timeline ({timeline.length})
          </span>
          {showTimeline ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showTimeline && timeline.length > 0 && (
          <div className="pt-2">
            <CustomerTimeline timeline={timeline} />
          </div>
        )}

        <button
          onClick={() => setShowTransfer(!showTransfer)}
          className="w-full py-1.5 px-2.5 text-xs text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg flex items-center justify-between transition"
        >
          <span className="flex items-center gap-1.5 font-medium">
            <ArrowRightLeft className="w-3.5 h-3.5 text-indigo-500" />
            Agent Continuity / Transfer
          </span>
          {showTransfer ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showTransfer && continuity && (
          <div className="pt-2">
            <AgentContinuityCard continuity={continuity} onTransfer={onTransfer} />
          </div>
        )}
      </div>
    </div>
  );
}
