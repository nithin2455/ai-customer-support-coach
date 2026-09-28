import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import {
  fetchMyConversations,
  createMyConversation,
  sendCustomerMessage
} from '../services/api';
import ChatWindow from '../components/ChatWindow';
import CustomerFeedbackModal from '../components/CustomerFeedbackModal';
import {
  User,
  MessageSquare,
  PlusCircle,
  LogOut,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Clock,
  Inbox
} from 'lucide-react';

export default function CustomerView() {
  const { user, logout } = useAuth();
  const [conversations, setConversations] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [apiError, setApiError] = useState(null);
  const [statusNotice, setStatusNotice] = useState(null);

  const loadData = useCallback(async (autoSelectFirst = false) => {
    try {
      setApiError(null);
      const data = await fetchMyConversations();
      setConversations(data);
      if (data.length > 0) {
        if (autoSelectFirst || !selectedId) {
          setSelectedId(data[0].id);
        }
      }
    } catch (err) {
      console.error('Error loading customer conversations:', err);
      setApiError('Unable to load your conversation history. Please refresh.');
    } finally {
      setIsLoading(false);
    }
  }, [selectedId]);

  useEffect(() => {
    loadData(true);
  }, []);

  const handleCreateNewConversation = async () => {
    try {
      setIsLoading(true);
      setApiError(null);
      const newConv = await createMyConversation();
      await loadData();
      setSelectedId(newConv.id);
      setStatusNotice(null);
    } catch (err) {
      console.error('Failed to create new conversation:', err);
      setApiError('Failed to start a new chat session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const activeConv = conversations.find((c) => c.id === selectedId) || conversations[0] || null;

  const handleSendCustomerMsg = async (content, languageCode, locale) => {
    if (!activeConv) {
      // If no conversation exists yet, automatically create one first
      try {
        setIsAnalyzing(true);
        const newConv = await createMyConversation();
        const res = await sendCustomerMessage(newConv.id, content, languageCode, locale);
        handleResponseNotice(res);
        await loadData();
        setSelectedId(newConv.id);
      } catch (err) {
        setApiError("Failed to send your message. Please try again.");
      } finally {
        setIsAnalyzing(false);
      }
      return;
    }

    try {
      setIsAnalyzing(true);
      setApiError(null);
      setStatusNotice(null);

      const res = await sendCustomerMessage(activeConv.id, content, languageCode, locale);
      handleResponseNotice(res);
      await loadData();
    } catch (err) {
      console.error('Error sending customer message:', err);
      setApiError("Sorry, we couldn't process your message right now. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleResponseNotice = (res) => {
    if (
      res.handling_mode === 'RULE_RESPONSE' ||
      res.handling_mode === 'LLM_RESPONSE' ||
      res.handling_mode === 'AI_AUTO_RESPONSE'
    ) {
      setStatusNotice({
        type: 'success',
        title: '✓ Answered by AI Support Assistant',
        desc: 'Your inquiry was answered instantly by our automated assistant.'
      });
    } else {
      setStatusNotice({
        type: 'info',
        title: '✓ Connected to Support',
        desc: "I've sent your request to a support specialist. They will review your details and respond shortly."
      });
    }
  };

  return (
    <div className="flex-1 flex h-[calc(100vh-57px)] bg-slate-50 overflow-hidden font-sans">
      {/* Left Sidebar: My Conversations History */}
      <aside className="w-80 bg-white border-r border-slate-200 flex flex-col shrink-0">
        {/* Sidebar Header */}
        <div className="p-4 border-b border-slate-200 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MessageSquare className="w-4 h-4 text-indigo-600" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">
                My Inquiries
              </h3>
            </div>
            <span className="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
              {conversations.length}
            </span>
          </div>

          <button
            type="button"
            onClick={handleCreateNewConversation}
            disabled={isLoading || isAnalyzing}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-medium text-xs py-2 px-3 rounded-lg transition flex items-center justify-center space-x-1.5 shadow-xs"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Inquiry</span>
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
          {isLoading ? (
            <div className="p-6 text-center text-slate-400 text-xs flex flex-col items-center space-y-2">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
              <span>Loading inquiries...</span>
            </div>
          ) : conversations.length === 0 ? (
            <div className="p-8 text-center text-slate-400 text-xs flex flex-col items-center space-y-2">
              <Inbox className="w-8 h-8 text-slate-300" />
              <p className="font-medium text-slate-600">No past inquiries</p>
              <p className="text-[11px] text-slate-400">
                Click &quot;New Inquiry&quot; above to start a conversation.
              </p>
            </div>
          ) : (
            conversations.map((conv) => {
              const isSelected = activeConv?.id === conv.id;
              const isResolved = conv.status === 'resolved';
              const lastMsg =
                conv.messages && conv.messages.length > 0
                  ? conv.messages[conv.messages.length - 1]
                  : null;

              return (
                <button
                  key={conv.id}
                  onClick={() => {
                    setSelectedId(conv.id);
                    setStatusNotice(null);
                  }}
                  className={`w-full text-left p-3 rounded-lg transition flex flex-col space-y-1.5 ${
                    isSelected
                      ? 'bg-indigo-50/80 border border-indigo-200'
                      : 'hover:bg-slate-50 border border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-900 text-xs">
                      Ticket #{conv.id}
                    </span>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        isResolved
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}
                    >
                      {isResolved ? 'Resolved' : 'Active'}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-600 line-clamp-2 leading-relaxed">
                    {lastMsg ? lastMsg.content : 'New inquiry started'}
                  </p>

                  <div className="flex items-center space-x-1 text-[10px] text-slate-400 pt-0.5">
                    <Clock className="w-3 h-3" />
                    <span>
                      {new Date(conv.created_at || Date.now()).toLocaleDateString([], {
                        month: 'short',
                        day: 'numeric'
                      })}
                    </span>
                  </div>
                </button>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Support Area */}
      <main className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
        {/* Top Customer Portal Banner */}
        <div className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 text-indigo-600 flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Support Session
                </h2>
                <span className="text-[10px] px-2 py-0.2 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Live Assistance
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Connected as <strong className="text-slate-700">{user?.name}</strong>{' '}
                <span className="text-slate-400 font-normal">({user?.tier || 'Standard'} Member)</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-medium text-slate-700">{user?.email}</p>
              <p className="text-[10px] text-slate-400">Authenticated Account</p>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="flex items-center space-x-1.5 px-3 py-1.5 bg-white hover:bg-rose-50 hover:text-rose-700 border border-slate-200 rounded-lg text-xs font-medium text-slate-600 transition"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Log Out</span>
            </button>
          </div>
        </div>

        {/* Workflow Status Banner */}
        {statusNotice && (
          <div
            className={`px-6 py-2.5 border-b text-xs flex items-center justify-between shrink-0 transition ${
              statusNotice.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-blue-50 border-blue-200 text-blue-800'
            }`}
          >
            <div className="flex items-center space-x-2">
              {statusNotice.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0" />
              )}
              <div>
                <span className="font-bold">{statusNotice.title}: </span>
                <span>{statusNotice.desc}</span>
              </div>
            </div>
            <button
              onClick={() => setStatusNotice(null)}
              className="text-[10px] text-slate-500 hover:text-slate-800 underline font-medium"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Chat Window */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <ChatWindow
            conversation={activeConv}
            onSendCustomerMessage={handleSendCustomerMsg}
            isCustomerView={true}
            isAnalyzing={isAnalyzing}
            apiError={apiError}
          />
        </div>

        {/* CSAT Feedback Area if resolved */}
        {activeConv && activeConv.status === 'resolved' && (
          <div className="bg-white border-t border-slate-200 p-4 shrink-0">
            <CustomerFeedbackModal
              conversationId={activeConv.id}
              onSubmitSuccess={() => loadData()}
            />
          </div>
        )}
      </main>
    </div>
  );
}
