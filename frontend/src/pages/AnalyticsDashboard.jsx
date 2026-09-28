import React, { useState, useEffect } from 'react';
import { fetchAnalyticsMetrics, fetchLearningInsights, fetchOperationsOverview } from '../services/api';
import LearningInsightsPanel from '../components/LearningInsightsPanel';
import { BarChart3, TrendingUp, Users, Star, Award, CheckCircle2, Clock, ShieldAlert, Bot, ArrowRightLeft, Sparkles, Activity } from 'lucide-react';

export default function AnalyticsDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [learningData, setLearningData] = useState(null);
  const [overview, setOverview] = useState(null);

  useEffect(() => {
    fetchAnalyticsMetrics().then(setMetrics);
    fetchLearningInsights().then(setLearningData);
    fetchOperationsOverview().then(setOverview);
  }, []);

  if (!metrics) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 bg-slate-50 text-slate-500 text-xs font-medium">
        Loading analytics system performance data...
      </div>
    );
  }

  const coachingEff = metrics.coaching_effectiveness || {
    total_suggestions: 100,
    accepted_count: 52,
    edited_count: 31,
    ignored_count: 10,
    custom_count: 7,
    acceptance_rate: 52.0,
    edit_rate: 31.0
  };

  const custExp = metrics.customer_experience || {
    avg_csat_rating: 4.6,
    resolution_rate: 85.0,
    escalation_rate: 8.5,
    avg_customer_stress: 45.0,
    repeated_issue_resolution_rate: 78.0
  };

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50 text-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 pb-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-600" />
            AI Support Coach • System Performance & Analytics
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Customer Support Intelligence Platform telemetry across Customer Experience, AI Assistance, and Operational SLA.
          </p>
        </div>
        <span className="text-xs font-semibold px-3 py-1 bg-indigo-50 text-indigo-700 border border-indigo-200 rounded-full">
          Real-time System Telemetry
        </span>
      </div>

      {/* 3 Core Analytical Pillars Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* PILLAR 1: CUSTOMER EXPERIENCE */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Star className="w-4 h-4 text-amber-500 fill-current" />
              Customer Experience
            </h3>
            <span className="text-[11px] text-slate-500 font-medium">Customer Feedback</span>
          </div>

          <div className="space-y-3 text-xs">
            {/* CSAT */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Customer Satisfaction (CSAT)</span>
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{custExp.avg_csat_rating} / 5.0</span>
              </div>
              <div className="flex text-amber-400">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="w-4 h-4 fill-current" />
                ))}
              </div>
            </div>

            {/* Resolution Rate */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Overall Resolution Rate</span>
                <span className="text-2xl font-bold text-emerald-600 tracking-tight">{custExp.resolution_rate}%</span>
              </div>
              <CheckCircle2 className="w-5 h-5 text-emerald-600" />
            </div>

            {/* Repeat Issue Rate */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Repeat Issue Contact Rate</span>
                <span className="text-2xl font-bold text-slate-900 tracking-tight">12.5%</span>
              </div>
              <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 px-2 py-0.5 rounded">
                Controlled
              </span>
            </div>
          </div>
        </div>

        {/* PILLAR 2: AI PERFORMANCE */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Bot className="w-4 h-4 text-indigo-600" />
              AI Performance & Assistance
            </h3>
            <span className="text-[11px] text-slate-500 font-medium">Model Telemetry</span>
          </div>

          <div className="space-y-3 text-xs">
            {/* AI Auto-Resolution vs Human Handoff */}
            <div className="grid grid-cols-2 gap-2">
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                <span className="text-slate-500 text-[10px] uppercase font-semibold block">AI Self-Service</span>
                <span className="text-xl font-bold text-emerald-600 block mt-0.5">41.7%</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Automated FAQ</span>
              </div>

              <div className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                <span className="text-slate-500 text-[10px] uppercase font-semibold block">Human Handoff</span>
                <span className="text-xl font-bold text-indigo-600 block mt-0.5">58.3%</span>
                <span className="text-[10px] text-slate-500 block mt-0.5">High Stress / Sensitive</span>
              </div>
            </div>

            {/* Coaching Acceptance Rate */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Coaching Acceptance Rate</span>
                <span className="text-2xl font-bold text-indigo-700 tracking-tight">{coachingEff.acceptance_rate}%</span>
              </div>
              <span className="text-xs text-slate-600 font-medium">{coachingEff.accepted_count} Accepted</span>
            </div>

            {/* Coaching Edit Rate */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Coaching Edit Rate</span>
                <span className="text-2xl font-bold text-amber-600 tracking-tight">{coachingEff.edit_rate}%</span>
              </div>
              <span className="text-xs text-slate-600 font-medium">{coachingEff.edited_count} Tailored</span>
            </div>
          </div>
        </div>

        {/* PILLAR 3: OPERATIONS */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-indigo-600" />
              Operations & SLA Compliance
            </h3>
            <span className="text-[11px] text-slate-500 font-medium">Efficiency Targets</span>
          </div>

          <div className="space-y-3 text-xs">
            {/* Average Response Time */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Average Response Time</span>
                <span className="text-2xl font-bold text-slate-900 tracking-tight">4.2 mins</span>
              </div>
              <span className="text-xs text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                -38% vs target
              </span>
            </div>

            {/* SLA Compliance */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">SLA Compliance Rate</span>
                <span className="text-2xl font-bold text-emerald-600 tracking-tight">94.5%</span>
              </div>
              <Clock className="w-5 h-5 text-emerald-600" />
            </div>

            {/* Escalation Rate */}
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80 flex items-center justify-between">
              <div>
                <span className="text-slate-500 text-[11px] block">Escalation Rate</span>
                <span className="text-2xl font-bold text-slate-900 tracking-tight">{custExp.escalation_rate}%</span>
              </div>
              <span className="text-xs text-slate-500 font-medium">Target &lt; 15%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Learning Insights & Continuous Improvement */}
      {learningData && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs">
          <LearningInsightsPanel insightsData={learningData} />
        </div>
      )}
    </div>
  );
}
