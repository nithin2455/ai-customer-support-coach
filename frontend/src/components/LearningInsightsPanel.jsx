import React from 'react';
import { Lightbulb, TrendingUp, AlertTriangle, CheckCircle2, ShieldCheck, Sparkles, Edit3 } from 'lucide-react';

export default function LearningInsightsPanel({ insightsData, insights: propInsights }) {
  const data = insightsData || propInsights;
  if (!data) return null;

  const insightsList = data.learning_insights || [];
  const topAccepted = data.top_accepted_patterns || [];
  const mostEdited = data.most_edited_patterns || [];
  const rejected = data.rejected_recommendations || [];
  const improvements = data.areas_requiring_improvement || [];

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-lg">
            <Lightbulb className="w-4 h-4 text-indigo-600" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">AI Continuous Learning & Insights</h3>
            <span className="text-[11px] text-slate-500 block">Feedback-driven coaching improvements and operational pattern analysis</span>
          </div>
        </div>
        <span className="text-[10px] px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold">
          Closed-Loop Learning Active
        </span>
      </div>

      {/* Structured Insights Cards */}
      <div className="grid grid-cols-2 gap-4">
        {insightsList.map((item, idx) => (
          <div key={item.id || idx} className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-xs hover:border-indigo-300 transition-colors">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <Sparkles className="w-4 h-4 text-indigo-600" />
                {item.title}
              </span>
              <span className="text-[10px] bg-slate-100 text-slate-700 font-medium px-2 py-0.5 rounded border border-slate-200">
                {(item.confidence_score * 100).toFixed(0)}% Confidence
              </span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                <span className="text-[10px] font-bold text-slate-500 block uppercase">Observed Pattern</span>
                <p className="text-slate-800 text-[11px] leading-relaxed">{item.pattern}</p>
              </div>

              <div className="bg-amber-50/60 p-2.5 rounded-lg border border-amber-200/60">
                <span className="text-[10px] font-bold text-amber-800 block uppercase">Learning Insight</span>
                <p className="text-slate-800 text-[11px] leading-relaxed">{item.insight}</p>
              </div>

              <div className="bg-indigo-50/50 p-2.5 rounded-lg border border-indigo-200/60">
                <span className="text-[10px] font-bold text-indigo-900 block uppercase flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-indigo-600" /> Controlled Improvement Recommendation
                </span>
                <p className="text-slate-800 text-[11px] font-medium leading-relaxed">{item.recommendation}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Pattern Categorization Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Top Accepted Patterns */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-xs">
          <h4 className="text-xs font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-emerald-600" /> Top Accepted Coaching Patterns
          </h4>
          <div className="space-y-2 text-xs">
            {topAccepted.map((p, i) => (
              <div key={i} className="bg-emerald-50/50 p-2.5 rounded-lg border border-emerald-100 flex items-start space-x-2">
                <span className="text-emerald-600 font-bold">•</span>
                <span className="text-slate-800 text-[11px] leading-relaxed">{p}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Most Edited Patterns */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 space-y-3 shadow-xs">
          <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
            <Edit3 className="w-4 h-4 text-amber-600" /> Most Edited Coaching Patterns
          </h4>
          <div className="space-y-2 text-xs">
            {mostEdited.map((p, i) => (
              <div key={i} className="bg-amber-50/50 p-2.5 rounded-lg border border-amber-100 flex items-start space-x-2">
                <span className="text-amber-600 font-bold">•</span>
                <span className="text-slate-800 text-[11px] leading-relaxed">{p}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
