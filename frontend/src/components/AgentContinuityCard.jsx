import React, { useState } from 'react';
import { UserCheck, ArrowRightLeft, ShieldCheck, Info } from 'lucide-react';

export default function AgentContinuityCard({ continuity, onTransfer }) {
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [selectedAgentId, setSelectedAgentId] = useState(2); // Michael Brown default
  const [transferReason, setTransferReason] = useState('Escalation to Logistics Specialist');

  if (!continuity) return null;

  const handleConfirmTransfer = () => {
    onTransfer(selectedAgentId, transferReason);
    setShowTransferModal(false);
  };

  return (
    <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2.5">
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center space-x-1.5">
          <UserCheck className="w-3.5 h-3.5 text-indigo-600" />
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-700">Agent Continuity</h3>
        </div>
        <button
          onClick={() => setShowTransferModal(true)}
          className="text-[11px] bg-white hover:bg-slate-100 text-indigo-700 px-2 py-1 rounded border border-slate-200 flex items-center gap-1 transition font-medium"
        >
          <ArrowRightLeft className="w-3 h-3" />
          <span>Transfer</span>
        </button>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-slate-400 block">Previous Agent</span>
          <span className="font-semibold text-slate-700">{continuity.previous_agent_name || 'Sarah Jenkins'}</span>
        </div>
        <div className="bg-white p-2 rounded border border-slate-200">
          <span className="text-[10px] text-slate-400 block">Current Agent</span>
          <span className="font-semibold text-indigo-700">{continuity.current_agent_name || 'Sarah Jenkins'}</span>
        </div>
      </div>

      <div className="bg-indigo-50/70 p-2.5 rounded border border-indigo-100 text-xs space-y-1">
        <span className="font-semibold text-indigo-800 flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" /> {continuity.continuity_status}
        </span>
        <p className="text-[11px] text-slate-600 leading-relaxed">{continuity.continuity_recommendation}</p>
      </div>

      {continuity.is_transferred && continuity.transfer_context && (
        <div className="bg-white p-2.5 rounded border border-slate-200 space-y-1 text-xs">
          <span className="text-indigo-700 font-bold block text-[11px]">Transferred Context Summary:</span>
          <p className="text-[11px] text-slate-600">
            <strong>Reason:</strong> {continuity.transfer_context.reason}
          </p>
          <p className="text-[11px] text-slate-600">
            <strong>Next Action:</strong> {continuity.transfer_context.recommended_next_action}
          </p>
        </div>
      )}

      {/* Transfer Modal */}
      {showTransferModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-slate-200 rounded-xl p-5 max-w-md w-full space-y-3 shadow-lg">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ArrowRightLeft className="w-4 h-4 text-indigo-600" />
              Transfer Conversation & Context Summary
            </h3>

            <p className="text-xs text-slate-500 leading-relaxed">
              Compiles customer context, repeated issue history, and stress score to transfer to the receiving agent.
            </p>

            <div className="space-y-2 text-xs">
              <label className="text-slate-700 font-medium block">Select Receiving Agent:</label>
              <select
                value={selectedAgentId}
                onChange={(e) => setSelectedAgentId(Number(e.target.value))}
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 focus:outline-none focus:border-indigo-600"
              >
                <option value={2}>Michael Brown (Logistics Specialist)</option>
                <option value={1}>Sarah Jenkins (Senior Support Agent)</option>
              </select>

              <label className="text-slate-700 font-medium block pt-1">Transfer Reason / Notes:</label>
              <input
                type="text"
                value={transferReason}
                onChange={(e) => setTransferReason(e.target.value)}
                placeholder="Reason for transfer..."
                className="w-full bg-white border border-slate-300 rounded-lg p-2 text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowTransferModal(false)}
                className="px-3.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-lg transition"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmTransfer}
                className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg transition shadow-xs"
              >
                Confirm Transfer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
