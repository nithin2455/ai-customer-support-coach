import React from 'react';
import { Sparkles, CheckCircle2, MessageSquare, AlertOctagon, Heart, CornerDownLeft, EyeOff, Compass, ShieldAlert, History, HelpCircle } from 'lucide-react';
import StressGauge from './StressGauge';

export default function CoachingPanel({ coaching, analysis, customer, onApplySuggestion, onIgnoreSuggestion }) {
  if (!coaching && !analysis) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-5 text-center text-slate-400">
        <Sparkles className="w-6 h-6 mx-auto mb-1.5 text-slate-400" />
        <p className="text-xs">Waiting for customer message to generate AI coaching recommendations...</p>
      </div>
    );
  }

  const stressScore = customer?.current_stress_score || analysis?.stress_score || 0;
  const strategy = coaching?.coaching_strategy;
  const styleLabel = analysis?.communication_style || customer?.predicted_style || 'Direct';

  return (
    <div className="bg-white border border-slate-200 rounded-lg p-3.5 space-y-3 shadow-xs overflow-y-auto max-h-[85vh] text-slate-800">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-2">
        <div className="flex items-center space-x-1.5">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-800">
              AI Coaching Assistant
            </h2>
            <span className="text-[10px] text-slate-400 block">Agent retains final decision control</span>
          </div>
        </div>
        <span className="text-[10px] px-2 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">
          Active
        </span>
      </div>

      {/* Stress Score Gauge */}
      <StressGauge score={stressScore} />

      {/* Communication Style & NLP Badges */}
      {analysis && (
        <div className="grid grid-cols-3 gap-1.5 text-center text-xs">
          <div className="bg-slate-50 p-2 rounded border border-slate-200">
            <span className="text-[10px] text-slate-400 block">Intent</span>
            <span className="font-semibold text-slate-800 truncate block text-[11px]">{analysis.intent}</span>
          </div>
          <div className="bg-slate-50 p-2 rounded border border-slate-200">
            <span className="text-[10px] text-slate-400 block">Sentiment</span>
            <span className={`font-semibold text-[11px] ${analysis.sentiment === 'Negative' ? 'text-rose-600' : 'text-emerald-600'}`}>
              {analysis.sentiment}
            </span>
          </div>
          <div className="bg-slate-50 p-2 rounded border border-slate-200">
            <span className="text-[10px] text-slate-400 block">Comm. Style</span>
            <span className="font-semibold text-slate-700 truncate block text-[11px]">{styleLabel}</span>
          </div>
        </div>
      )}

      {/* Warning Banner */}
      {coaching?.warning && (
        <div className={`p-2.5 rounded border text-xs flex items-start space-x-2 ${
          coaching.escalation_required
            ? 'bg-rose-50 border-rose-200 text-rose-800'
            : 'bg-amber-50 border-amber-200 text-amber-800'
        }`}>
          <AlertOctagon className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
          <div>
            <span className="font-bold block text-[11px]">Customer Alert</span>
            <p className="text-[11px] leading-relaxed">{coaching.warning}</p>
          </div>
        </div>
      )}

      {/* Personalized AI Coaching Strategy Card */}
      {strategy && (
        <div className="bg-slate-50 border border-slate-200 rounded-lg p-2.5 space-y-2">
          <div className="flex items-center justify-between border-b border-slate-200 pb-1.5">
            <span className="text-[11px] font-bold text-slate-700 flex items-center gap-1 uppercase tracking-wider">
              <Compass className="w-3.5 h-3.5 text-indigo-600" />
              Strategy & Tone
            </span>
            <span className="text-[10px] px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">
              {strategy.empathy_level} Empathy
            </span>
          </div>
          
          <div className="grid grid-cols-2 gap-1.5 text-[11px]">
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] text-slate-400 block">Recommended Tone</span>
              <span className="font-medium text-slate-800">{strategy.tone}</span>
            </div>
            <div className="bg-white p-2 rounded border border-slate-200">
              <span className="text-[10px] text-slate-400 block">Response Length</span>
              <span className="font-medium text-slate-800">{strategy.response_length}</span>
            </div>
          </div>

          {strategy.avoid && (
            <div className="bg-rose-50 border border-rose-200 p-2 rounded text-[11px] text-rose-800">
              <span className="font-semibold block text-[10px] text-rose-700 uppercase">What to Avoid</span>
              {strategy.avoid}
            </div>
          )}
        </div>
      )}

      {/* Coaching Rationale */}
      {(coaching?.coaching_reason || strategy?.explanation) && (
        <div className="bg-slate-50 p-2.5 rounded border border-slate-200 text-xs space-y-1">
          <span className="font-semibold text-slate-700 flex items-center gap-1 text-[11px]">
            <HelpCircle className="w-3.5 h-3.5 text-indigo-600" />
            Coaching Rationale
          </span>
          <p className="text-slate-600 text-[11px] leading-relaxed">
            {coaching?.coaching_reason || strategy?.explanation}
          </p>
        </div>
      )}

      {/* Suggested Response Card */}
      {coaching?.suggested_response && (
        <div className="bg-white border border-indigo-200 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
              <MessageSquare className="w-3.5 h-3.5 text-indigo-600" />
              Suggested Response
            </span>
            <span className="text-[10px] bg-indigo-50 text-indigo-700 px-1.5 py-0.2 rounded border border-indigo-200 font-medium">Draft</span>
          </div>

          <p className="text-xs text-slate-800 bg-slate-50 p-2.5 rounded border border-slate-200 leading-relaxed italic">
            "{coaching.suggested_response}"
          </p>

          <div className="flex items-center gap-1.5 pt-0.5">
            <button
              onClick={() => onApplySuggestion(coaching.suggested_response, 'accepted')}
              className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium py-1.5 px-3 rounded flex items-center justify-center space-x-1 transition shadow-xs"
            >
              <CornerDownLeft className="w-3 h-3" />
              <span>Use Suggestion</span>
            </button>
            <button
              onClick={() => onApplySuggestion(coaching.suggested_response, 'edited')}
              className="bg-white hover:bg-slate-50 text-slate-700 text-xs font-medium py-1.5 px-3 rounded border border-slate-200 transition"
            >
              Edit
            </button>
            <button
              onClick={() => onIgnoreSuggestion()}
              className="bg-white hover:bg-slate-50 text-slate-500 hover:text-slate-700 text-xs font-medium py-1.5 px-2 rounded border border-slate-200 transition"
              title="Ignore suggestion"
            >
              <EyeOff className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
