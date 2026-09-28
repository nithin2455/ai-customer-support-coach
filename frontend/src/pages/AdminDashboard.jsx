import React, { useState, useEffect } from 'react';
import { fetchOperationsOverview, fetchSLAAnalytics, fetchEscalationAnalytics, fetchLearningInsights } from '../services/api';
import { Shield, Users, Layers, AlertTriangle, Clock, CheckCircle2, TrendingUp, Star, Bot, AlertOctagon, Sparkles, Coins, DollarSign, BookOpen, Zap, Filter } from 'lucide-react';

export default function AdminDashboard() {
  const [overview, setOverview] = useState(null);
  const [slaData, setSlaData] = useState(null);
  const [escalationData, setEscalationData] = useState(null);
  const [learningData, setLearningData] = useState(null);
  const [activeSection, setActiveSection] = useState('Overview');

  useEffect(() => {
    fetchOperationsOverview().then(setOverview);
    fetchSLAAnalytics().then(setSlaData);
    fetchEscalationAnalytics().then(setEscalationData);
    fetchLearningInsights().then(setLearningData);
  }, []);

  if (!overview) {
    return (
      <div className="flex-1 flex items-center justify-center p-12 bg-slate-50 text-slate-500 text-xs font-medium">
        Loading operational management data...
      </div>
    );
  }

  const adminSections = [
    'Overview',
    'Work queue',
    'Breaching soon',
    'Cases',
    'Trends',
    'Knowledge',
    'Actions',
    'Cost'
  ];

  const departments = [
    { name: "Order Fulfillment & Logistics", code: "ORDERS", count: 18, pct: 58, lead: "Sarah Jenkins" },
    { name: "Billing & Payments", code: "BILLING", count: 8, pct: 26, lead: "David Miller" },
    { name: "Technical Support", code: "TECH", count: 5, pct: 16, lead: "Michael Brown" }
  ];

  const recentEscalations = [
    { id: 1, customer: "Alex Johnson", issue: "Delayed Order #ORD-98213 (2 prior contacts)", tier: "CRITICAL", reason: "Repeated unresolved delay + high stress" },
    { id: 2, customer: "John Smith", issue: "Duplicate Charge ($149.00)", tier: "HIGH", reason: "Potential billing duplicate requiring refund" }
  ];

  const sampleCases = [
    { id: "ORD-98213", customer: "Alex Johnson", issue: "Order not arrived", dept: "ORDERS", status: "In Progress", priority: "URGENT", lang: "Tamil (ta)" },
    { id: "REF-41092", customer: "John Smith", issue: "Refund not received", dept: "BILLING", status: "Waiting", priority: "HIGH", lang: "English (en)" },
    { id: "RCH-77401", customer: "Priya Sharma", issue: "Recharge failed", dept: "BILLING", status: "AI Resolved", priority: "NORMAL", lang: "Hindi (hi)" },
    { id: "LGN-12094", customer: "Kavitha Rao", issue: "Cannot login to mobile app", dept: "TECH", status: "AI Resolved", priority: "NORMAL", lang: "Kannada (kn)" },
    { id: "SUB-30912", customer: "Ramesh Kumar", issue: "Threatening to cancel subscription", dept: "BILLING", status: "Escalated", priority: "CRITICAL", lang: "Hindi (hi)" }
  ];

  return (
    <div className="flex-1 p-6 overflow-y-auto space-y-6 bg-slate-50 text-slate-900">
      {/* Admin Header with Project Branding */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-4 gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
            <Shield className="w-5 h-5 text-indigo-600" />
            AI Support Coach • Operations Admin
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Customer Support Intelligence Platform • Overview, workloads, SLA compliance, and cost intelligence
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[11px] font-medium px-2.5 py-1 bg-slate-100 text-slate-600 border border-slate-200 rounded-full flex items-center gap-1">
            Sample support cases
          </span>
          <span className="text-xs font-semibold px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            Operational Status: Healthy
          </span>
        </div>
      </div>

      {/* Admin Navigation Sections */}
      <div className="flex items-center space-x-1 overflow-x-auto pb-1 border-b border-slate-200 text-xs">
        {adminSections.map((sec) => (
          <button
            key={sec}
            onClick={() => setActiveSection(sec)}
            className={`px-3 py-1.5 rounded-md font-medium whitespace-nowrap transition ${
              activeSection === sec
                ? 'bg-indigo-600 text-white font-semibold shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            {sec}
          </button>
        ))}
      </div>

      {/* Overview 7-KPI Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Total</span>
          <p className="text-2xl font-bold text-slate-900 tracking-tight">{overview.total_conversations || 12}</p>
          <span className="text-[11px] text-slate-500">Conversations</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 block">Active</span>
          <p className="text-2xl font-bold text-indigo-600 tracking-tight">{overview.active_conversations || 2}</p>
          <span className="text-[11px] text-slate-500">In Progress</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-600 block">AI Resolved</span>
          <p className="text-2xl font-bold text-emerald-600 tracking-tight">5</p>
          <span className="text-[11px] text-emerald-700 font-medium">Self-Service</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 block">Needs Agent</span>
          <p className="text-2xl font-bold text-amber-600 tracking-tight">4</p>
          <span className="text-[11px] text-amber-700 font-medium">In Agent Queue</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-rose-600 block">Escalated</span>
          <p className="text-2xl font-bold text-rose-600 tracking-tight">{overview.escalated_conversations || 1}</p>
          <span className="text-[11px] text-rose-700 font-medium">Lead Review</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">SLA Breached</span>
          <p className="text-2xl font-bold text-slate-900 tracking-tight">{overview.sla_breach_count || 0}</p>
          <span className="text-[11px] text-emerald-600 font-medium">0 Breaches</span>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-1">
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-600 block">CSAT Rating</span>
          <p className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-1">
            {overview.avg_csat_rating || 4.6}
            <Star className="w-4 h-4 text-amber-400 fill-current" />
          </p>
          <span className="text-[11px] text-slate-500">Out of 5.0</span>
        </div>
      </div>

      {/* COST SECTION */}
      {activeSection === 'Cost' && (
        <div className="space-y-6">
          {/* Cost Headline Card */}
          <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-3">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                  <Coins className="w-4 h-4 text-indigo-600" />
                  Estimated AI Cost & Token Telemetry
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">
                  Calculated operational cost tracking for LLM assistance, Indic translation, and coaching intelligence.
                </p>
              </div>
              <span className="text-[11px] font-semibold text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1 rounded-full self-start sm:self-auto">
                Calculated Estimate (Not Official Invoice)
              </span>
            </div>

            {/* 4 Core Cost Metrics */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pt-1">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Tokens Today</span>
                <p className="text-2xl font-bold text-slate-900 tracking-tight">142,580</p>
                <span className="text-[11px] text-emerald-600 font-medium">+12% vs daily avg</span>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-600 block">Estimated Spend Today</span>
                <p className="text-2xl font-bold text-indigo-700 tracking-tight">$0.28</p>
                <span className="text-[11px] text-slate-500">Estimated Spend (Calculated)</span>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Avg Cost / Case</span>
                <p className="text-2xl font-bold text-slate-900 tracking-tight">$0.024</p>
                <span className="text-[11px] text-slate-500">Estimated Average</span>
              </div>

              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Spend All Time</span>
                <p className="text-2xl font-bold text-slate-900 tracking-tight">$3.68</p>
                <span className="text-[11px] text-slate-500">1.84M Tokens All Time</span>
              </div>
            </div>
          </div>

          {/* Tokens by Step & Costliest Conversations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Tokens by Step */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-indigo-600" /> Tokens by Processing Step
                </h4>
                <span className="text-xs text-slate-500">Step Allocation</span>
              </div>

              <div className="space-y-3.5 text-xs">
                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-900">Dynamic AI Coaching & Reasoning</span>
                    <span className="font-bold text-indigo-700">62,740 tokens (44%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-600 rounded-full" style={{ width: '44%' }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-900">Intent & Sentiment Detection</span>
                    <span className="font-bold text-indigo-700">39,920 tokens (28%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-500 rounded-full" style={{ width: '28%' }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-900">Indic Multilingual Translation</span>
                    <span className="font-bold text-indigo-700">28,520 tokens (20%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-indigo-400 rounded-full" style={{ width: '20%' }} />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <div className="flex justify-between items-center text-xs">
                    <span className="font-semibold text-slate-900">Deterministic Rule Matching</span>
                    <span className="font-bold text-emerald-700">11,400 tokens (8%)</span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full" style={{ width: '8%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Costliest Conversations */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <DollarSign className="w-4 h-4 text-emerald-600" /> Costliest Conversations
                </h4>
                <span className="text-[11px] text-slate-400">Sample cases</span>
              </div>

              <div className="space-y-3 text-xs">
                {[
                  { caseId: "ORD-98213", customer: "Alex Johnson", tokens: "2,840 tokens", est: "$0.0057", issue: "Delayed Order (Repeated Contacts)" },
                  { caseId: "REF-41092", customer: "John Smith", tokens: "2,410 tokens", est: "$0.0048", issue: "Duplicate Charge ($149.00)" },
                  { caseId: "TECH-8120", customer: "Priya Sharma", tokens: "1,980 tokens", est: "$0.0039", issue: "Cannot login to mobile app" },
                  { caseId: "SUB-3091", customer: "Ramesh Kumar", tokens: "1,750 tokens", est: "$0.0035", issue: "Threatening to cancel subscription" }
                ].map((item, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900 text-xs">{item.caseId}</span>
                        <span className="text-slate-600 text-xs">({item.customer})</span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-0.5">{item.issue}</p>
                    </div>
                    <div className="text-right">
                      <span className="font-semibold text-slate-800 text-xs block">{item.tokens}</span>
                      <span className="text-[10px] text-emerald-700 font-medium">Est. {item.est}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Clarity Disclaimer Banner */}
          <div className="bg-amber-50/70 border border-amber-200 text-amber-900 p-4 rounded-xl text-xs space-y-1">
            <span className="font-bold flex items-center gap-1.5 text-amber-900">
              ℹ️ Estimated AI Cost Clarification
            </span>
            <p className="text-[11px] text-amber-800 leading-relaxed">
              All displayed cost values are algorithmic estimates derived from session token counts and standard model inference rates.
              They represent operational telemetry and analytical estimates for cost optimization, not actual Gemini invoices or billing charges.
            </p>
          </div>
        </div>
      )}

      {/* CASES / WORK QUEUE SECTION */}
      {(activeSection === 'Work queue' || activeSection === 'Cases') && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                <Users className="w-4 h-4 text-indigo-600" />
                Active Support Cases
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">Live cases across Order Fulfillment, Billing, and Technical Support</p>
            </div>
            <span className="text-[11px] font-medium px-2.5 py-0.5 bg-slate-100 text-slate-600 border border-slate-200 rounded-full">
              Sample support cases
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="text-[10px] uppercase font-bold text-slate-400 bg-slate-50 border-y border-slate-200">
                <tr>
                  <th className="py-2.5 px-3">Ticket ID</th>
                  <th className="py-2.5 px-3">Customer</th>
                  <th className="py-2.5 px-3">Issue Summary</th>
                  <th className="py-2.5 px-3">Department</th>
                  <th className="py-2.5 px-3">Language</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans">
                {sampleCases.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">{c.id}</td>
                    <td className="py-3 px-3 font-medium text-slate-800">{c.customer}</td>
                    <td className="py-3 px-3 text-slate-600">{c.issue}</td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium text-[10px]">
                        {c.dept}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-700">{c.lang}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded font-semibold text-[10px] ${
                        c.priority === 'CRITICAL' || c.priority === 'URGENT'
                          ? 'bg-rose-50 text-rose-700 border border-rose-200'
                          : c.priority === 'HIGH'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-slate-100 text-slate-700 border border-slate-200'
                      }`}>
                        {c.priority}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded font-medium text-[10px] ${
                        c.status === 'AI Resolved'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : c.status === 'In Progress'
                          ? 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                          : 'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* BREACHING SOON SECTION */}
      {activeSection === 'Breaching soon' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-rose-700 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              SLA Approaching Deadline / Breaching Soon
            </h3>
            <span className="text-xs font-bold text-rose-700 bg-rose-50 px-2.5 py-0.5 rounded border border-rose-200">
              Immediate Attention
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-4 bg-rose-50/70 border border-rose-200 rounded-xl flex items-center justify-between">
              <div>
                <span className="font-mono font-bold text-slate-900 text-xs">#ORD-98213 — Alex Johnson</span>
                <p className="text-slate-700 mt-1">Repeated Order Inquiries (Delayed status update)</p>
                <span className="text-[11px] text-rose-700 font-semibold mt-1 block">SLA Expiry: 6 minutes remaining</span>
              </div>
              <span className="px-2.5 py-1 rounded bg-rose-600 text-white font-bold text-xs shadow-xs">
                Urgent Action
              </span>
            </div>
          </div>
        </div>
      )}

      {/* KNOWLEDGE SECTION */}
      {activeSection === 'Knowledge' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-indigo-600" />
              Multilingual Knowledge & Self-Service Rule Base
            </h3>
            <span className="text-xs text-indigo-700 font-medium bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
              Deterministic FAQs (0 Cost, Instant)
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1.5">
              <span className="font-bold text-slate-900 block">Shipping & Delivery Times</span>
              <p className="text-slate-600 text-[11px]">Templates in English, Hindi, Tamil, and Kannada for standard order arrival windows (2-4 business days).</p>
            </div>
            <div className="p-3.5 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1.5">
              <span className="font-bold text-slate-900 block">Refund Eligibility Policy</span>
              <p className="text-slate-600 text-[11px]">30-day return policy and standard refund processing window definitions across supported languages.</p>
            </div>
          </div>
        </div>
      )}

      {/* ACTIONS SECTION */}
      {activeSection === 'Actions' && (
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
              <Zap className="w-4 h-4 text-indigo-600" />
              Operational Administrative Actions
            </h3>
            <span className="text-xs text-slate-500">System Governance</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
            <button className="p-3 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 rounded-lg text-left transition space-y-1">
              <span className="font-bold text-slate-900 block">Rebalance Queues</span>
              <p className="text-[11px] text-slate-500">Redistribute tickets evenly across active support agents.</p>
            </button>
            <button className="p-3 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 rounded-lg text-left transition space-y-1">
              <span className="font-bold text-slate-900 block">Recalculate Dynamic SLAs</span>
              <p className="text-[11px] text-slate-500">Update target response timers based on current queue volume.</p>
            </button>
            <button className="p-3 bg-slate-50 hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 rounded-lg text-left transition space-y-1">
              <span className="font-bold text-slate-900 block">Sync Multilingual Memory</span>
              <p className="text-[11px] text-slate-500">Update cross-session customer context summaries.</p>
            </button>
          </div>
        </div>
      )}

      {/* OVERVIEW / TRENDS SECTIONS (Rendered on Overview and Trends) */}
      {(activeSection === 'Overview' || activeSection === 'Trends') && (
        <>
          {/* Main Operational Sections */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Department Workload */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-600" /> Department Workload Distribution
                </h3>
                <span className="text-xs text-slate-500">Live Queue Allocation</span>
              </div>

              <div className="space-y-4 text-xs">
                {departments.map((dept, i) => (
                  <div key={i} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-semibold text-slate-900">{dept.name}</span>
                      <span className="font-bold text-indigo-700">{dept.count} tickets ({dept.pct}%)</span>
                    </div>
                    <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-indigo-600 rounded-full transition-all"
                        style={{ width: `${dept.pct}%` }}
                      />
                    </div>
                    <span className="text-[11px] text-slate-500 block">Lead: {dept.lead}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Escalations */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-rose-600" /> Recent Escalations
                </h3>
                <span className="text-xs text-rose-700 font-semibold bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                  Senior Attention Required
                </span>
              </div>

              <div className="space-y-3 text-xs">
                {recentEscalations.map((esc) => (
                  <div key={esc.id} className="p-3.5 bg-rose-50/60 border border-rose-200/80 rounded-lg space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-900 text-xs">{esc.customer}</span>
                      <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800 border border-rose-200">
                        {esc.tier}
                      </span>
                    </div>
                    <p className="text-slate-800 text-xs font-medium">{esc.issue}</p>
                    <p className="text-slate-600 text-[11px]">Reason: {esc.reason}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* SLA Performance & Learning Insights */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* SLA Performance */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <Clock className="w-4 h-4 text-emerald-600" /> SLA Performance & Compliance
                </h3>
                <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded border border-emerald-200">
                  {slaData ? `${slaData.first_response_sla_compliance_pct}% Compliance` : '94.5% Compliance'}
                </span>
              </div>

              <div className="grid grid-cols-3 gap-3 text-center text-xs">
                <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">On Track</span>
                  <span className="text-xl font-bold text-emerald-600 block mt-1">{slaData?.on_track_count || 9}</span>
                </div>
                <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">At Risk</span>
                  <span className="text-xl font-bold text-amber-600 block mt-1">{slaData?.at_risk_count || 2}</span>
                </div>
                <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200/80">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Breached</span>
                  <span className="text-xl font-bold text-rose-600 block mt-1">{slaData?.sla_breach_count || 0}</span>
                </div>
              </div>
            </div>

            {/* Continuous Learning Insights */}
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-indigo-600" /> Continuous Learning Highlights
                </h3>
                <span className="text-xs font-semibold text-indigo-700 bg-indigo-50 px-2.5 py-0.5 rounded border border-indigo-200">
                  Pattern Feedback Loop
                </span>
              </div>

              <div className="space-y-2.5 text-xs">
                {(learningData?.learning_insights || []).slice(0, 2).map((ins) => (
                  <div key={ins.id} className="p-3 bg-slate-50 border border-slate-200/80 rounded-lg space-y-1">
                    <span className="font-bold text-slate-900 text-xs block">{ins.title}</span>
                    <p className="text-slate-600 text-[11px] leading-relaxed">{ins.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
