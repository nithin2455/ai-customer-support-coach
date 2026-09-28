import React, { useState, useEffect } from 'react';
import { fetchConversations, sendCustomerMessage, sendAgentReply, sendCoachingFeedback, transferConversation } from '../services/api';
import ChatWindow from '../components/ChatWindow';
import CustomerContextPanel from '../components/CustomerContextPanel';
import { MessageSquare, RefreshCw, CheckCircle2, AlertCircle, Clock, Filter, UserCheck, ShieldAlert, Globe } from 'lucide-react';
import { getLanguageByCode } from '../config/languages';

export default function AgentDashboard() {
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [draftText, setDraftText] = useState('');
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [filterTab, setFilterTab] = useState('all'); // 'all', 'needs_agent', 'ai_resolved'

  const loadData = async () => {
    try {
      setLoading(true);
      setApiError(null);
      const data = await fetchConversations();
      setConversations(data);
      if (data.length > 0 && !selectedId) {
        setSelectedId(data[0].id);
      }
    } catch (err) {
      setApiError("Failed to fetch conversations from server.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const activeConv = conversations.find((c) => c.id === selectedId) || conversations[0];

  const handleSendCustomerMsg = async (content) => {
    if (!activeConv) return;
    try {
      setIsAnalyzing(true);
      setApiError(null);
      await sendCustomerMessage(activeConv.id, content);
      await loadData();
    } catch (err) {
      console.error("Error analyzing message:", err);
      setApiError("Failed to analyze customer message.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSendAgentReply = async (content, actionType) => {
    if (!activeConv) return;
    try {
      setApiError(null);
      const suggestedResp = activeConv.latest_coaching?.suggested_response || null;
      await sendAgentReply(activeConv.id, content, actionType, suggestedResp);
      setDraftText('');
      await loadData();
    } catch (err) {
      console.error("Error sending agent reply:", err);
      setApiError("Failed to deliver agent response.");
    }
  };

  const handleTransfer = async (newAgentId, reason) => {
    if (!activeConv) return;
    try {
      setApiError(null);
      await transferConversation(activeConv.id, newAgentId, reason);
      await loadData();
    } catch (err) {
      console.error("Error transferring conversation:", err);
      setApiError("Failed to transfer conversation.");
    }
  };

  const handleApplySuggestion = async (suggestion, actionType) => {
    setDraftText(suggestion);
    if (activeConv && activeConv.messages?.length > 0) {
      const lastMsg = activeConv.messages[activeConv.messages.length - 1];
      await sendCoachingFeedback(activeConv.id, lastMsg.id, actionType, suggestion, suggestion);
    }
  };

  const handleIgnoreSuggestion = async () => {
    setDraftText('');
    if (activeConv && activeConv.messages?.length > 0) {
      const lastMsg = activeConv.messages[activeConv.messages.length - 1];
      await sendCoachingFeedback(activeConv.id, lastMsg.id, 'ignored', '', '');
    }
  };

  const fullCtx = activeConv?.full_context || {};
  const repeatedIssue = fullCtx.repeated_issue || (activeConv?.latest_coaching?.is_repeated_issue ? {
    is_repeated_issue: true,
    issue_type: activeConv.latest_coaching.issue_type,
    reason: activeConv.latest_coaching.warning
  } : null);

  const continuity = fullCtx.agent_continuity || {
    current_agent_name: activeConv?.agent?.name || 'Sarah Jenkins',
    previous_agent_name: activeConv?.previous_agent?.name || 'Sarah Jenkins',
    is_transferred: activeConv?.is_transferred,
    continuity_status: 'Previous Agent Available',
    continuity_recommendation: 'Agent Continuity Maintained.',
    transfer_context: activeConv?.transfer_context
  };

  const timeline = fullCtx.timeline || [];
  const slaInfo = fullCtx.sla_info || { status: 'On Track', first_response_target_minutes: 30, resolution_target_minutes: 240 };
  const escalationInfo = fullCtx.escalation_info || {
    escalation_recommended: activeConv?.latest_coaching?.escalation_required || false,
    escalation_tier: 'HIGH',
    reasons_list: [activeConv?.latest_coaching?.warning || 'High priority customer review recommended'],
    recommended_action: activeConv?.latest_coaching?.escalation_recommendation || 'Provide concrete status update'
  };

  // Filtered Queue
  const filteredConversations = conversations.filter((c) => {
    const isResolved = c.status === 'resolved';
    if (filterTab === 'ai_resolved') return isResolved;
    if (filterTab === 'needs_agent') return !isResolved;
    return true;
  });

  const formatQueueTime = (dateStr) => {
    if (!dateStr) return 'Just now';
    const diffMs = Date.now() - new Date(dateStr).getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h`;
    return `${Math.floor(diffHours / 24)}d`;
  };

  return (
    <div className="flex-1 flex overflow-hidden h-[calc(100vh-57px)] bg-slate-50 text-slate-900">
      {/* ===================================================
          COLUMN 1 — SUPPORT QUEUE (Compact & Clean)
          =================================================== */}
      <div className="w-72 bg-white border-r border-slate-200 flex flex-col shrink-0">
        {/* Queue Header */}
        <div className="p-3.5 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MessageSquare className="w-4 h-4 text-indigo-600" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-700">Support Queue</h2>
            <span className="text-[10px] bg-slate-100 text-slate-600 font-bold px-1.5 py-0.5 rounded-full">
              {conversations.length}
            </span>
            <span className="text-[9px] bg-slate-100 text-slate-500 font-medium px-1.5 py-0.5 rounded border border-slate-200" title="Demonstration support queue cases">
              Sample cases
            </span>
          </div>
          <button
            onClick={loadData}
            className="p-1 text-slate-400 hover:text-slate-700 rounded hover:bg-slate-100 transition"
            title="Refresh Queue"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="px-3 pt-2.5 pb-2 border-b border-slate-100 flex items-center gap-1 text-[11px]">
          <button
            onClick={() => setFilterTab('all')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              filterTab === 'all'
                ? 'bg-indigo-50 text-indigo-700 font-semibold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            All
          </button>
          <button
            onClick={() => setFilterTab('needs_agent')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              filterTab === 'needs_agent'
                ? 'bg-rose-50 text-rose-700 font-semibold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Needs Agent
          </button>
          <button
            onClick={() => setFilterTab('ai_resolved')}
            className={`px-2.5 py-1 rounded-md font-medium transition ${
              filterTab === 'ai_resolved'
                ? 'bg-emerald-50 text-emerald-700 font-semibold'
                : 'text-slate-500 hover:text-slate-800'
            }`}
          >
            Resolved
          </button>
        </div>

        {/* Queue Conversation List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100">
          {filteredConversations.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400">
              No tickets in this filter.
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isSelected = conv.id === activeConv?.id;
              const cust = conv.customer;
              const isResolved = conv.status === 'resolved';
              const priority = conv.priority || 'NORMAL';
              const isHigh = priority === 'URGENT' || priority === 'HIGH';

              // Priority style
              const priorityLabel = isHigh ? 'High' : 'Normal';

              // Status style
              const statusTag = isResolved
                ? { label: 'Resolved', class: 'bg-emerald-50 text-emerald-700 border-emerald-200' }
                : isHigh
                  ? { label: 'Waiting for agent', class: 'bg-rose-50 text-rose-700 border-rose-200' }
                  : { label: 'Waiting', class: 'bg-amber-50 text-amber-700 border-amber-200' };

              const lastMessage = conv.messages && conv.messages.length > 0
                ? conv.messages[conv.messages.length - 1].content
                : 'No messages yet';

              return (
                <button
                  key={conv.id}
                  onClick={() => setSelectedId(conv.id)}
                  className={`w-full text-left p-3 transition flex flex-col space-y-1 ${
                    isSelected
                      ? 'bg-indigo-50/70 border-l-4 border-indigo-600'
                      : 'hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-900">{cust?.name}</span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {formatQueueTime(conv.created_at)}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 truncate leading-snug">
                    {lastMessage}
                  </p>

                  <div className="flex items-center justify-between text-[10px] pt-1">
                    <div className="flex items-center gap-1.5">
                      <span className={`font-medium ${isHigh ? 'text-rose-600 font-semibold' : 'text-slate-500'}`}>
                        {priorityLabel}
                      </span>
                      {conv.language_code && conv.language_code !== 'en' && (
                        <span className="bg-indigo-50 text-indigo-700 px-1.5 py-0.2 rounded font-medium border border-indigo-200">
                          {getLanguageByCode(conv.language_code).name}
                        </span>
                      )}
                    </div>
                    <span className={`text-[10px] font-medium px-1.5 py-0.2 rounded border ${statusTag.class}`}>
                      {statusTag.label}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* ===================================================
          COLUMN 2 — MAIN CONVERSATION (Dominant Area)
          Chat Thread + Conversational AI Coaching + Agent Response
          =================================================== */}
      <ChatWindow
        conversation={activeConv}
        onSendCustomerMessage={handleSendCustomerMsg}
        onSendAgentReply={handleSendAgentReply}
        draftText={draftText}
        setDraftText={setDraftText}
        isCustomerView={false}
        isAnalyzing={isAnalyzing}
        apiError={apiError}
        onApplySuggestion={handleApplySuggestion}
        onIgnoreSuggestion={handleIgnoreSuggestion}
      />

      {/* ===================================================
          COLUMN 3 — CUSTOMER CONTEXT (Compact Supporting Context)
          Customer tier, interactions, style, stress, repeated issue, SLA, escalation
          =================================================== */}
      <CustomerContextPanel
        customer={activeConv?.customer}
        slaInfo={slaInfo}
        escalationInfo={escalationInfo}
        repeatedIssue={repeatedIssue}
        continuity={continuity}
        timeline={timeline}
        onTransfer={handleTransfer}
      />
    </div>
  );
}
