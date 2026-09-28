import React from 'react';
import { Clock, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';

export default function SLABadge({ sla }) {
  if (!sla) return null;

  const status = sla.status || 'On Track';
  const priority = sla.priority || 'HIGH';
  const respMins = sla.first_response_target_minutes || 30;
  const resMins = sla.resolution_target_minutes || 240;

  let statusBg = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  let icon = <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />;

  if (status === 'At Risk') {
    statusBg = 'bg-amber-50 text-amber-700 border-amber-200';
    icon = <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />;
  } else if (status.includes('Breached')) {
    statusBg = 'bg-rose-50 text-rose-700 border-rose-200';
    icon = <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />;
  }

  const formatSecs = (sec) => {
    if (!sec || sec <= 0) return '0m';
    const m = Math.floor(sec / 60);
    if (m > 60) {
      const h = Math.floor(m / 60);
      return `${h}h ${m % 60}m`;
    }
    return `${m}m`;
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2 text-slate-800">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1.5">
          <Clock className="w-3.5 h-3.5 text-indigo-600" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-700">Dynamic SLA Status</span>
        </div>
        <span className={`text-[10px] font-medium px-2 py-0.5 rounded border flex items-center gap-1 ${statusBg}`}>
          {icon}
          {status} ({priority})
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[11px]">
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-slate-400 block">First Response Target</span>
          <span className="font-semibold text-slate-800">{respMins} mins</span>
          <span className="block text-[9px] text-slate-500 mt-0.5">
            Remaining: {formatSecs(sla.response_time_remaining_seconds)}
          </span>
        </div>

        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-slate-400 block">Resolution Target</span>
          <span className="font-semibold text-slate-800">{resMins >= 60 ? `${resMins/60} hrs` : `${resMins} mins`}</span>
          <span className="block text-[9px] text-slate-500 mt-0.5">
            Remaining: {formatSecs(sla.resolution_time_remaining_seconds)}
          </span>
        </div>
      </div>
    </div>
  );
}
