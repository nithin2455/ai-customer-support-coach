import React, { useState, useRef, useEffect } from 'react';
import { Send, UserCheck, User, Bot, Sparkles, AlertCircle, Loader2, CheckCircle2, CornerDownLeft, EyeOff, ShieldAlert, Compass, Globe, Cpu } from 'lucide-react';
import VoiceInputButton from './VoiceInputButton';
import VoiceOutputButton from './VoiceOutputButton';
import { SUPPORTED_LANGUAGES, getLanguageByCode } from '../config/languages';
import { fetchConfiguredModel } from '../services/api';

function formatLocalTime(timestamp) {
  if (!timestamp) return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  let str = String(timestamp);
  if (!str.endsWith('Z') && !str.includes('+') && !str.includes('-', 10)) {
    str += 'Z';
  }
  return new Date(str).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

export default function ChatWindow({
  conversation,
  onSendCustomerMessage,
  onSendAgentReply,
  draftText,
  setDraftText,
  isCustomerView = false,
  isAnalyzing = false,
  apiError = null,
  onApplySuggestion,
  onIgnoreSuggestion
}) {
  const [custInput, setCustInput] = useState('');
  const [agentInput, setAgentInput] = useState('');
  const [actionType, setActionType] = useState('custom');
  const [selectedLang, setSelectedLang] = useState(() => (
    conversation?.language_code
      ? getLanguageByCode(conversation.language_code)
      : SUPPORTED_LANGUAGES[0]
  ));
  const [modelName, setModelName] = useState('gemini-3.5-flash');
  const messagesEndRef = useRef(null);
  const agentTextareaRef = useRef(null);

  useEffect(() => {
    fetchConfiguredModel().then(setModelName);
  }, []);

  useEffect(() => {
    if (conversation?.language_code) {
      setSelectedLang(getLanguageByCode(conversation.language_code));
    }
  }, [conversation?.language_code]);

  useEffect(() => {
    if (draftText !== undefined && draftText !== null) {
      setAgentInput(draftText);
      setActionType('edited');
      if (agentTextareaRef.current && draftText) {
        agentTextareaRef.current.focus();
      }
    }
  }, [draftText]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation?.messages, isAnalyzing]);

  const handleCustSubmit = (e) => {
    e.preventDefault();
    if (!custInput.trim()) return;
    onSendCustomerMessage(custInput, selectedLang.code, selectedLang.locale);
    setCustInput('');
  };

  const handleAgentSubmit = (e) => {
    e.preventDefault();
    if (!agentInput.trim()) return;
    onSendAgentReply(agentInput, actionType);
    setAgentInput('');
    if (setDraftText) setDraftText('');
    setActionType('custom');
  };

  const handleUseSuggestion = (suggestion) => {
    setAgentInput(suggestion);
    setActionType('accepted');
    if (onApplySuggestion) onApplySuggestion(suggestion, 'accepted');
  };

  const handleEditSuggestion = (suggestion) => {
    setAgentInput(suggestion);
    setActionType('edited');
    if (onApplySuggestion) onApplySuggestion(suggestion, 'edited');
    if (agentTextareaRef.current) agentTextareaRef.current.focus();
  };

  const handleIgnore = () => {
    setAgentInput('');
    setActionType('custom');
    if (onIgnoreSuggestion) onIgnoreSuggestion();
  };

  if (!conversation) {
    return (
      <div className="flex-1 bg-slate-50 flex items-center justify-center text-slate-400 text-sm">
        Select an active conversation to view message history.
      </div>
    );
  }

  const customer = conversation.customer;
  const latestAssistantMessage = conversation?.messages?.length
    ? [...conversation.messages].reverse().find((m) => m.sender_type === 'assistant')
    : null;
  const isAutoResolved = conversation.status === 'resolved';
  const coaching = conversation.latest_coaching;
  const priority = conversation.priority || 'NORMAL';

  // Priority color
  const priorityClass = priority === 'URGENT' || priority === 'HIGH'
    ? 'bg-rose-50 text-rose-700 border-rose-200'
    : priority === 'NORMAL'
      ? 'bg-slate-100 text-slate-700 border-slate-200'
      : 'bg-slate-100 text-slate-600 border-slate-200';

  // Status badge
  const statusClass = isAutoResolved
    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
    : priority === 'URGENT' || priority === 'HIGH'
      ? 'bg-rose-50 text-rose-700 border-rose-200'
      : 'bg-amber-50 text-amber-700 border-amber-200';

  const statusLabel = isAutoResolved
    ? 'AI Resolved'
    : priority === 'URGENT' || priority === 'HIGH'
      ? 'Needs Agent'
      : 'Waiting';

  // Extract order reference if any
  let orderRef = null;
  const combinedText = (conversation.messages || []).map(m => m.content).join(' ');
  const orderMatch = combinedText.match(/#?(\d{5}|ORD-\d+)/);
  if (orderMatch) {
    orderRef = `#${orderMatch[1].replace('#', '')}`;
  } else if (customer?.name === 'Alex Johnson') {
    orderRef = '#98213';
  }

  return (
    <div className="flex-1 flex flex-col bg-slate-50 border-x border-slate-200 h-full overflow-hidden">
      {/* Header bar */}
      <div className="bg-white border-b border-slate-200 px-5 py-3 flex items-center justify-between shrink-0 shadow-sm">
        {isCustomerView ? (
          /* Customer Portal Header */
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-indigo-600 flex items-center justify-center text-white shadow-sm">
              <Bot className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                Customer Support
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block animate-pulse" />
              </h2>
              <p className="text-xs text-slate-500">Support Assistant • Instant answers for general queries & agent assistance</p>
            </div>
          </div>
        ) : (
          /* Agent Workspace Header */
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-indigo-600 to-indigo-700 flex items-center justify-center font-bold text-white shadow-sm text-sm">
              {customer?.name?.charAt(0) || 'C'}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">{customer?.name || 'Customer'}</h2>
                {orderRef && (
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200 font-mono font-semibold">
                    Order {orderRef}
                  </span>
                )}
                <span className="text-[11px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 font-medium">
                  {conversation.department_name || 'General Support'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {customer?.email} • {customer?.tier || 'Standard'} Customer
              </p>
            </div>
          </div>
        )}

        {/* Status badges */}
        {!isCustomerView && (
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
              <Globe className="w-3 h-3 text-indigo-500" />
              Language: {getLanguageByCode(conversation.language_code).name}
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200" title="Configured Gemini Model">
              <Cpu className="w-3 h-3 text-indigo-600" />
              Model: Gemini {modelName}
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border ${priorityClass}`}>
              {priority} Priority
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold border flex items-center gap-1 ${statusClass}`}>
              {isAutoResolved && <CheckCircle2 className="w-3 h-3 text-emerald-600" />}
              {statusLabel}
            </span>
          </div>
        )}
      </div>

      {/* Error Banner */}
      {apiError && (
        <div className="bg-rose-50 border-b border-rose-200 text-rose-700 px-4 py-2 text-xs flex items-center space-x-2 shrink-0">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{apiError}</span>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-slate-50/50">
        {conversation.messages?.length === 0 ? (
          <div className="text-center text-slate-400 text-xs py-12">
            No messages in this chat yet. Type a question below to begin.
          </div>
        ) : (
          conversation.messages.map((msg) => {
            const isCustomer = msg.sender_type === 'customer';
            const isAssistant = msg.sender_type === 'assistant';

            return (
              <div
                key={msg.id}
                className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'}`}
              >
                {/* Sender Title and Timestamp */}
                <div className="flex items-center space-x-1.5 mb-1 px-1">
                  <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                    {isCustomer ? (
                      <>
                        <User className="w-3 h-3 text-slate-600" />
                        {isCustomerView ? 'You' : customer?.name}
                      </>
                    ) : isAssistant ? (
                      <>
                        <Bot className="w-3 h-3 text-indigo-600" />
                        Support Assistant
                        {!isCustomerView && (
                          <span className="text-[9px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-1 rounded font-normal">
                            AI Auto-Response
                          </span>
                        )}
                      </>
                    ) : (
                      <>
                        <UserCheck className="w-3 h-3 text-indigo-600" />
                        Support Agent
                      </>
                    )}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    {formatLocalTime(msg.created_at)}
                  </span>
                </div>

                {/* Message Bubble */}
                {!isCustomerView && isCustomer ? (
                  /* Customer Message in Agent Console */
                  <div className="max-w-[85%] rounded-xl p-3.5 text-xs leading-relaxed bg-white text-slate-800 border border-slate-200 rounded-tr-none shadow-2xs space-y-2.5">
                    {msg.language_code && msg.language_code !== 'en' ? (
                      <>
                        <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                            Customer Language
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {getLanguageByCode(msg.language_code).name} ({getLanguageByCode(msg.language_code).nativeName})
                          </span>
                        </div>

                        <div className="space-y-2">
                          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                            <span className="font-bold text-[10px] text-slate-500 block uppercase tracking-wider mb-1">
                              Original Customer Message
                            </span>
                            <p className="text-slate-900 text-xs font-medium leading-relaxed font-sans">
                              {msg.original_content || msg.content}
                            </p>
                          </div>

                          <div className="bg-indigo-50/70 p-2.5 rounded-lg border border-indigo-200/80">
                            <span className="font-bold text-[10px] text-indigo-700 block uppercase tracking-wider mb-1">
                              English Translation
                            </span>
                            <p className="text-slate-900 text-xs leading-relaxed font-sans">
                              {msg.translated_content || msg.content}
                            </p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-slate-900 font-sans">{msg.content}</div>
                    )}
                  </div>
                ) : !isCustomerView && !isCustomer && !isAssistant ? (
                  /* Agent Response in Agent Console */
                  <div className="max-w-[85%] rounded-xl p-3.5 text-xs leading-relaxed bg-white text-slate-800 border border-indigo-200 rounded-tl-none shadow-2xs space-y-2.5">
                    {msg.language_code && msg.language_code !== 'en' && msg.original_content && msg.original_content !== msg.content ? (
                      <>
                        <div className="flex items-center justify-between pb-1.5 border-b border-slate-100">
                          <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">
                            Customer Language
                          </span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                            {getLanguageByCode(msg.language_code).name}
                          </span>
                        </div>

                        <div className="space-y-2">
                          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                            <span className="font-bold text-[10px] text-slate-500 block uppercase tracking-wider mb-1">
                              Agent Response (English)
                            </span>
                            <p className="text-slate-900 text-xs leading-relaxed font-sans">
                              {msg.original_content}
                            </p>
                          </div>

                          <div className="bg-emerald-50/70 p-2.5 rounded-lg border border-emerald-200/80">
                            <span className="font-bold text-[10px] text-emerald-800 block uppercase tracking-wider mb-1">
                              Customer Receives ({getLanguageByCode(msg.language_code).name})
                            </span>
                            <p className="text-slate-900 text-xs leading-relaxed font-sans">
                              {msg.content}
                            </p>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="text-slate-900 font-sans">{msg.content}</div>
                    )}
                  </div>
                ) : (
                  /* Customer View or Assistant Auto-Response */
                  <div
                    className={`max-w-[78%] rounded-xl px-4 py-2.5 text-xs leading-relaxed ${
                      isCustomer
                        ? 'bg-indigo-600 text-white rounded-tr-none'
                        : 'bg-white text-slate-800 border border-slate-200 rounded-tl-none shadow-2xs'
                    }`}
                  >
                    <div>{msg.content}</div>

                    {/* Voice Output Button on Assistant Response */}
                    {isAssistant && (
                      <div className="flex items-center justify-end mt-2 pt-1.5 border-t border-slate-100">
                        <VoiceOutputButton
                          text={msg.content}
                          selectedLanguage={msg.language_code || selectedLang.code}
                        />
                      </div>
                    )}
                  </div>
                )}

                {/* Internal NLP Analysis Tag underneath Customer message (AGENT VIEW ONLY) */}
                {!isCustomerView && isCustomer && msg.ai_analysis && (
                  <div className="mt-1 flex items-center space-x-2 text-[10px] text-slate-400 px-1 font-sans">
                    <span className="font-semibold text-indigo-600">{msg.ai_analysis.intent}</span>
                    <span>•</span>
                    <span className={msg.ai_analysis.sentiment === 'Negative' ? 'text-rose-600 font-semibold' : 'text-emerald-600'}>
                      {msg.ai_analysis.sentiment}
                    </span>
                    <span>•</span>
                    <span>Stress: {msg.ai_analysis.stress_score}/100</span>
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* Loading Indicator */}
        {isAnalyzing && (
          <div className="flex items-center space-x-2 text-indigo-700 text-xs bg-indigo-50 p-3 rounded-xl border border-indigo-100 animate-pulse">
            <Loader2 className="w-4 h-4 animate-spin text-indigo-600" />
            <span>Support Assistant is processing message...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* BOTTOM AREA: Copilot + Input Controls */}
      <div className="bg-white border-t border-slate-200 p-4 shrink-0 space-y-3">
        {isCustomerView ? (
          /* ===================================================
             CUSTOMER VIEW INPUT (Clean customer support chat)
             =================================================== */
          <form onSubmit={handleCustSubmit} className="space-y-2.5">
            {/* Language Selector */}
            <div className="flex items-center justify-between px-0.5">
              <div className="flex items-center gap-1.5">
                <Globe className="w-3.5 h-3.5 text-indigo-600" />
                <span className="text-[11px] font-semibold text-slate-600">Language:</span>
                <select
                  value={selectedLang.code}
                  onChange={(e) => setSelectedLang(getLanguageByCode(e.target.value))}
                  className="bg-slate-50 hover:bg-slate-100 border border-slate-300 rounded-md px-2 py-1 text-xs text-slate-800 font-semibold focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 cursor-pointer"
                  aria-label="Select support language"
                >
                  {SUPPORTED_LANGUAGES.map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name} ({lang.nativeName})
                    </option>
                  ))}
                </select>
              </div>
              <span className="text-[11px] text-slate-400 hidden sm:inline">
                Voice input & speech output configured for {selectedLang.name} ({selectedLang.nativeName})
              </span>
            </div>

            {/* Message input */}
            <div className="w-full">
              <input
                type="text"
                value={custInput}
                onChange={(e) => setCustInput(e.target.value)}
                placeholder={`Type your message or speak in ${selectedLang.name} (${selectedLang.nativeName})...`}
                className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 transition shadow-2xs"
              />
            </div>

            {/* Action Buttons Row: [ 🎤 Voice ] [ 🔊 Voice Output ] [ Send ] */}
            <div className="flex items-center justify-between pt-0.5">
              <div className="flex items-center gap-2">
                <VoiceInputButton
                  selectedLanguage={selectedLang}
                  onTranscript={(transcript) => {
                    setCustInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
                  }}
                  disabled={isAnalyzing}
                  showLabel={true}
                  label="Voice"
                />

                <VoiceOutputButton
                  text={
                    latestAssistantMessage?.content ||
                    custInput ||
                    "Welcome to AI Support Coach. Please type or speak your question."
                  }
                  selectedLanguage={latestAssistantMessage?.language_code || selectedLang}
                  showLabel={true}
                  label="Voice Output"
                  activeLabel="Stop Audio"
                />
              </div>

              <button
                type="submit"
                disabled={!custInput.trim() || isAnalyzing}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold text-xs px-5 py-2 rounded-lg flex items-center space-x-1.5 transition shadow-xs"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
          </form>
        ) : (
          /* ===================================================
             AGENT DASHBOARD CONTROLS (Column 2 dominant workflow)
             =================================================== */
          <div className="space-y-3">
            {/* 1. If AI Auto-Resolved */}
            {isAutoResolved ? (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 flex items-center justify-between text-xs text-emerald-800">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  <div>
                    <span className="font-semibold block">Automatically Resolved by Automated Assistant</span>
                    <p className="text-[11px] text-emerald-700">Self-service FAQ completed. No agent intervention required.</p>
                  </div>
                </div>
                <span className="text-[10px] uppercase font-semibold text-emerald-700 bg-emerald-100/70 px-2 py-0.5 rounded border border-emerald-300">
                  Resolved
                </span>
              </div>
            ) : (
              /* 2. Professional AI Coaching Assistant Panel */
              coaching && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 space-y-2 text-xs">
                  <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
                    <span className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                      AI Coaching
                    </span>
                    <span className="text-[10px] text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.2 rounded font-medium">
                      Assistant Suggestion
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-[10px] text-slate-500 font-medium block">Recommended Tone</span>
                      <span className="font-semibold text-slate-700">
                        {coaching.coaching_strategy?.tone || 'Concise and empathetic'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 font-medium block">Priority</span>
                      <span className="font-semibold text-slate-700">
                        {priority || 'Normal'}
                      </span>
                    </div>
                  </div>

                  {/* Suggested Response */}
                  {coaching.suggested_response && (
                    <div className="bg-white p-2.5 rounded border border-slate-200 space-y-2">
                      <span className="text-[10px] font-semibold text-slate-500 block uppercase">
                        Suggested Response
                      </span>
                      <p className="text-slate-800 text-[11px] leading-relaxed italic">
                        "{coaching.suggested_response}"
                      </p>
                      <div className="flex items-center gap-1.5 pt-0.5">
                        <button
                          type="button"
                          onClick={() => handleUseSuggestion(coaching.suggested_response)}
                          className="bg-indigo-600 hover:bg-indigo-700 text-white text-[11px] font-medium px-2.5 py-1 rounded flex items-center space-x-1 transition"
                        >
                          <CornerDownLeft className="w-3 h-3" />
                          <span>Use suggestion</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => handleEditSuggestion(coaching.suggested_response)}
                          className="bg-white hover:bg-slate-100 text-slate-700 text-[11px] font-medium px-2.5 py-1 rounded border border-slate-200 transition"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={handleIgnore}
                          className="bg-white hover:bg-slate-100 text-slate-500 hover:text-slate-700 text-[11px] font-medium px-2 py-1 rounded border border-slate-200 transition"
                          title="Ignore suggestion"
                        >
                          Ignore
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Why this suggestion */}
                  {(coaching.coaching_reason || coaching.warning) && (
                    <div className="text-[11px] pt-0.5">
                      <span className="text-[10px] font-medium text-slate-400 uppercase block">Why this suggestion?</span>
                      <p className="text-slate-600 text-[11px] leading-snug">
                        {coaching.coaching_reason || coaching.warning}
                      </p>
                    </div>
                  )}
                </div>
              )
            )}

            {/* 3. Agent Final Response Box */}
            <form onSubmit={handleAgentSubmit} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 flex items-center gap-1.5">
                  <UserCheck className="w-3.5 h-3.5 text-indigo-600" />
                  Agent Final Response
                </span>
                <span className="text-[10px] text-slate-400">Agent retains final decision control</span>
              </div>

              <div className="flex items-start gap-2">
                <textarea
                  ref={agentTextareaRef}
                  value={agentInput}
                  onChange={(e) => {
                    setAgentInput(e.target.value);
                    if (setDraftText) setDraftText(e.target.value);
                  }}
                  rows={2}
                  placeholder="Review AI suggestion, edit, or write your final response here..."
                  className="flex-1 bg-white border border-slate-300 focus:border-indigo-600 focus:ring-1 focus:ring-indigo-600 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none transition resize-none"
                />
                <button
                  type="submit"
                  disabled={!agentInput.trim()}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-xs px-4 py-2 rounded-lg flex items-center space-x-1.5 transition shadow-xs h-[54px]"
                >
                  <span>Send Response</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
