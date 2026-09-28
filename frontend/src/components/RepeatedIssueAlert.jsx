import React from 'react';
import { RotateCcw, AlertTriangle, CheckSquare } from 'lucide-react';

export default function RepeatedIssueAlert({ repeatedIssue }) {
  if (!repeatedIssue || !repeatedIssue.is_repeated_issue) return null;

  return (
    <div className="bg-rose-50 border border-rose-200 rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1 bg-rose-100 text-rose-600 rounded">
            <RotateCcw className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-800">
              Repeated Issue Detected
            </h3>
            <span className="text-[10px] text-rose-600 font-medium block">
              {repeatedIssue.issue_type}
            </span>
          </div>
        </div>
        <span className="text-[10px] bg-rose-100 text-rose-800 font-semibold px-2 py-0.5 rounded border border-rose-300">
          Unresolved Priority
        </span>
      </div>

      <p className="text-xs text-rose-900 bg-white p-2 rounded border border-rose-200 leading-relaxed">
        {repeatedIssue.reason}
      </p>

      <div className="text-[11px] text-slate-700 space-y-0.5 bg-white p-2 rounded border border-rose-100">
        <span className="font-semibold text-rose-700 block text-[10px] uppercase">Coaching Guideline:</span>
        <p className="text-slate-600 text-[10px] leading-normal">
          Do not ask customer to repeat basic troubleshooting already attempted. Provide immediate status resolution.
        </p>
      </div>
    </div>
  );
}
