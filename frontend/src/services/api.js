const API_BASE = '/api/v1';

export function getAuthToken() {
  return localStorage.getItem('auth_token');
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem('auth_token', token);
  } else {
    localStorage.removeItem('auth_token');
  }
}

export function authHeaders(customHeaders = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...customHeaders
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to sign in. Please check your credentials.');
  }
  const data = await res.json();
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function registerCustomer(name, email, password, confirmPassword) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      email,
      password,
      confirm_password: confirmPassword
    })
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Registration failed. Please check your details.');
  }
  const data = await res.json();
  if (data.access_token) {
    setAuthToken(data.access_token);
  }
  return data;
}

export async function fetchCurrentUser() {
  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
}

export async function logoutUser() {
  try {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: authHeaders()
    });
  } catch (e) {
    // Ignore network error on logout
  } finally {
    setAuthToken(null);
  }
}

export async function fetchMyConversations() {
  const res = await fetch(`${API_BASE}/chat/customer/me/conversations`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
}

export async function createMyConversation() {
  const res = await fetch(`${API_BASE}/chat/customer/me/conversations`, {
    method: 'POST',
    headers: authHeaders()
  });
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
}

export async function fetchMyOrders() {
  const res = await fetch(`${API_BASE}/chat/customer/me/orders`, {
    headers: authHeaders()
  });
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
}

export async function fetchConversations() {
  try {
    const res = await fetch(`${API_BASE}/chat/conversations`, {
      headers: authHeaders()
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API connection offline, using fallback mock data:', err);
    return getFallbackConversations();
  }
}

export async function fetchConversationById(id) {
  try {
    const res = await fetch(`${API_BASE}/chat/conversation/${id}`, {
      headers: authHeaders()
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API connection offline for get conversation:', err);
    const fallback = getFallbackConversations();
    return fallback.find(c => c.id === Number(id)) || fallback[0];
  }
}

export async function fetchCustomerById(id) {
  try {
    const res = await fetch(`${API_BASE}/chat/customer/${id}`, {
      headers: authHeaders()
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('API connection offline for get customer:', err);
    return getFallbackConversations()[0].customer;
  }
}

export async function transferConversation(conversationId, newAgentId, reason = 'Specialization transfer') {
  const res = await fetch(`${API_BASE}/chat/conversation/${conversationId}/transfer`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ new_agent_id: newAgentId, reason })
  });
  if (!res.ok) throw new Error(`Failed to transfer conversation (HTTP ${res.status})`);
  return await res.json();
}

export async function sendCustomerMessage(conversationId, content, languageCode = null, locale = null) {
  const payload = {
    conversation_id: conversationId,
    content,
    sender_type: 'customer'
  };
  if (languageCode) {
    payload.language_code = languageCode;
  }
  if (locale) {
    payload.locale = locale;
  }
  const res = await fetch(`${API_BASE}/chat/message`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to process message (HTTP ${res.status})`);
  return await res.json();
}

export const sendChatMessage = sendCustomerMessage;

export async function translateTextApi(text, sourceLanguage, targetLanguage) {
  const res = await fetch(`${API_BASE}/chat/translate`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      text,
      source_language: sourceLanguage,
      target_language: targetLanguage
    })
  });
  if (!res.ok) throw new Error(`Failed to translate text (HTTP ${res.status})`);
  return await res.json();
}

export async function sendAgentReply(conversationId, content, actionType = 'custom', suggestedResp = null) {
  const res = await fetch(`${API_BASE}/chat/agent-reply`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      conversation_id: conversationId,
      content,
      action_type: actionType,
      suggested_response: suggestedResp
    })
  });
  if (!res.ok) throw new Error(`Failed to send agent reply (HTTP ${res.status})`);
  return await res.json();
}

export async function sendCoachingFeedback(conversationId, messageId, action, suggestedResp, actualResp) {
  try {
    const res = await fetch(`${API_BASE}/coaching/feedback`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        conversation_id: conversationId,
        message_id: messageId,
        agent_action: action,
        suggested_response: suggestedResp,
        actual_response: actualResp
      })
    });
    return await res.json();
  } catch (err) {
    console.error('Failed to submit coaching feedback:', err);
  }
}

export async function submitCustomerFeedback(conversationId, csatRating, comments = '', outcome = 'Resolved') {
  try {
    const res = await fetch(`${API_BASE}/coaching/csat`, {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        conversation_id: conversationId,
        csat_rating: csatRating,
        comments,
        outcome
      })
    });
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Failed to submit customer feedback:', err);
    return { status: 'success', csat_id: 99, rating: csatRating, outcome };
  }
}

export async function fetchAnalyticsMetrics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/metrics`);
    if (!res.ok) throw new Error('Failed to fetch analytics');
    return await res.json();
  } catch (err) {
    console.warn('API offline, returning mock analytics');
    return {
      total_conversations: 35,
      active_tickets: 4,
      avg_csat_rating: 4.7,
      avg_customer_stress: 68.5,
      coaching_adoption_rate_pct: 88.4,
      coaching_effectiveness: {
        total_suggestions: 100,
        accepted_count: 52,
        edited_count: 31,
        ignored_count: 10,
        custom_count: 7,
        acceptance_rate: 52.0,
        edit_rate: 31.0,
        rejection_rate: 10.0,
        custom_rate: 7.0
      },
      customer_experience: {
        avg_csat_rating: 4.5,
        resolution_rate: 87.0,
        escalation_rate: 10.0,
        avg_customer_stress: 45.0,
        repeated_issue_resolution_rate: 80.0
      },
      sentiment_distribution: { negative: 62, neutral: 24, positive: 14 },
      intents_breakdown: {
        "Order Delay / Logistics": 18,
        "Billing & Payments": 8,
        "Technical Issue": 5,
        "General Inquiry": 4
      }
    };
  }
}

export async function fetchLearningInsights() {
  try {
    const res = await fetch(`${API_BASE}/analytics/insights`);
    if (!res.ok) throw new Error('Failed to fetch learning insights');
    return await res.json();
  } catch (err) {
    console.warn('API offline, returning mock learning insights');
    return {
      learning_insights: [
        {
          id: "INSIGHT-01",
          title: "High-Stress Customer Response Personalization",
          pattern: "High-stress customers show a higher rate of edited AI responses (Edit rate 31%).",
          insight: "Agents frequently shorten and personalize AI recommendations further for customers displaying severe frustration.",
          recommendation: "Prefer concise de-escalation statements and immediate concrete next steps for stress levels above 80.",
          confidence_score: 0.92,
          affected_category: "Stress Management"
        },
        {
          id: "INSIGHT-02",
          title: "Order Delay Specificity Enhancement",
          pattern: "Order-delay coaching suggestions are frequently edited by agents before sending.",
          insight: "Agents consistently modify order-delay responses to append specific carrier tracking links or dispatch timelines.",
          recommendation: "Include concrete delivery status and carrier tracking reference when available in logistics context.",
          confidence_score: 0.88,
          affected_category: "Logistics & Shipping"
        },
        {
          id: "INSIGHT-03",
          title: "Repeated Issue De-Escalation Priority",
          pattern: "Repeated issue contacts have lower first-touch resolution rates when basic troubleshooting is repeated.",
          insight: "Customers contacting support 2+ times respond negatively to repetitive diagnostics.",
          recommendation: "Prioritize prior resolution review and escalation guidance immediately upon repeated issue detection.",
          confidence_score: 0.95,
          affected_category: "Customer Retention"
        }
      ],
      top_accepted_patterns: [
        "Empathetic validation for first-time order inquiries",
        "Structured bullet breakdowns for analytical inquiries"
      ],
      areas_requiring_improvement: [
        "Proactive logistics status lookup integration",
        "Refined de-escalation phrasing for 80+ stress tiers"
      ]
    };
  }
}

export async function fetchOperationsOverview() {
  try {
    const res = await fetch(`${API_BASE}/analytics/overview`);
    if (!res.ok) throw new Error('Failed to fetch operations overview');
    return await res.json();
  } catch (err) {
    console.warn('API offline, returning mock operations overview');
    return {
      total_conversations: 12,
      active_conversations: 2,
      high_priority_conversations: 3,
      escalated_conversations: 1,
      sla_breach_count: 0,
      avg_csat_rating: 4.6,
      resolution_rate: 80.0,
      coaching_adoption_rate: 85.0
    };
  }
}

export async function fetchSLAAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/sla`);
    if (!res.ok) throw new Error('Failed to fetch SLA analytics');
    return await res.json();
  } catch (err) {
    console.warn('API offline, returning mock SLA analytics');
    return {
      first_response_sla_compliance_pct: 94.5,
      resolution_sla_compliance_pct: 88.2,
      sla_breach_count: 1,
      at_risk_count: 2,
      on_track_count: 9
    };
  }
}

export async function fetchEscalationAnalytics() {
  try {
    const res = await fetch(`${API_BASE}/analytics/escalation`);
    if (!res.ok) throw new Error('Failed to fetch escalation analytics');
    return await res.json();
  } catch (err) {
    console.warn('API offline, returning mock escalation analytics');
    return {
      escalation_count: 2,
      escalation_rate_pct: 10.0,
      escalations_by_department: {
        "Order Fulfillment & Logistics": 2,
        "Billing & Payments": 0,
        "Technical Support": 0
      },
      primary_escalation_triggers: [
        "Repeated unresolved order delay",
        "High stress score (>80/100)"
      ]
    };
  }
}

function getFallbackConversations() {
  return [
    {
      id: 1,
      customer: {
        id: 1,
        name: "Alex Johnson",
        email: "alex.j@example.com",
        phone: "+1 (555) 234-5678",
        tier: "VIP",
        badge: "Repeated Issue Customer",
        total_contacts: 3,
        unresolved_issues: 1,
        current_stress_score: 85,
        predicted_style: "Impatient / Direct",
        memories: [
          {
            id: 101,
            issue_summary: "Delayed delivery for Order #ORD-98213 (Shipped 8 days ago)",
            resolution_summary: "Issued $15 apology credit. Awaiting carrier delivery update.",
            sentiment_label: "Negative",
            agent_name: "Sarah Jenkins",
            created_at: "2026-09-01T10:00:00Z"
          }
        ]
      },
      agent: {
        id: 1,
        name: "Sarah Jenkins (Senior Agent)",
        email: "sarah.j@support.com",
        department_name: "Order Fulfillment & Logistics",
        status: "available",
        skill_level: "senior"
      },
      previous_agent: {
        id: 1,
        name: "Sarah Jenkins",
        email: "sarah.j@support.com",
        department_name: "Order Fulfillment & Logistics",
        status: "available",
        skill_level: "senior"
      },
      department_name: "Order Fulfillment & Logistics",
      status: "active",
      priority: "HIGH",
      is_transferred: false,
      created_at: new Date().toISOString(),
      messages: [
        {
          id: 1,
          conversation_id: 1,
          sender_type: "customer",
          content: "I've been waiting for my order for a week. This is very frustrating.",
          created_at: new Date().toISOString(),
          ai_analysis: {
            intent: "Order Delay / Logistics",
            sentiment: "Negative",
            sentiment_score: 0.92,
            emotion: "Frustration",
            topic: "Order Status",
            language: "English",
            stress_score: 85,
            communication_style: "Impatient / Direct"
          }
        }
      ],
      latest_coaching: {
        warning: "🔄 REPEATED ISSUE DETECTED (Repeated Issue) • STRESS 85/100 (HIGH): Customer previously contacted support regarding order delay. Do NOT ask customer to repeat basic troubleshooting.",
        is_repeated_issue: true,
        issue_type: "Repeated Issue",
        recommended_actions: [
          "Acknowledge that the issue has happened again and validate customer frustration.",
          "Review previous troubleshooting & logistics escalation steps already taken.",
          "Avoid asking the customer to repeat already completed troubleshooting.",
          "Check whether further escalation to Senior Operations is required.",
          "Provide a clear, concrete status update and timeline."
        ],
        empathy_guidance: "Acknowledge prior touchpoints. Customer is frustrated about repeating an unresolved problem. Recommend brief, direct answers with immediate action items.",
        resolution_guidance: "Goal: Swift resolution of Repeated Issue (Order Delay / Logistics). Ensure concrete update is delivered.",
        suggested_response: "I completely understand how frustrating it is to deal with this order delay again, especially since you already contacted us about it. I have reviewed your previous report and am checking the logistics escalation right now to give you a concrete update.",
        escalation_required: true,
        customer_history_snippet: "VIP Customer | Total Contacts: 3 | Previous Issue: Delayed delivery for Order #ORD-98213"
      },
      full_context: {
        repeated_issue: {
          is_repeated_issue: true,
          issue_type: "Repeated Issue",
          reason: "Customer previously contacted support 2 times regarding the same order delay."
        },
        agent_continuity: {
          current_agent_name: "Sarah Jenkins",
          previous_agent_name: "Sarah Jenkins",
          continuity_status: "Previous Agent Available & Assigned",
          continuity_recommendation: "Agent Continuity Maintained (Sarah Jenkins)."
        },
        timeline: [
          { step: "Touchpoint 1", date: "2026-09-01", issue: "Order delayed by 2 days", sentiment: "Negative", stress_score: 65, agent: "Sarah Jenkins", resolution: "Issued $15 credit" },
          { step: "Touchpoint 2", date: "2026-09-05", issue: "Order still delayed after 5 days", sentiment: "Negative", stress_score: 80, agent: "Sarah Jenkins", resolution: "Escalated to logistics" }
        ]
      }
    },
    {
      id: 2,
      customer: {
        id: 2,
        name: "Priya Kumar",
        email: "priya.k@example.com",
        phone: "+1 (555) 876-5432",
        tier: "Standard",
        badge: "Returning Customer",
        total_contacts: 1,
        unresolved_issues: 0,
        current_stress_score: 15,
        predicted_style: "Calm",
        memories: []
      },
      agent: {
        id: 1,
        name: "Sarah Jenkins",
        email: "sarah.j@support.com",
        department_name: "Order Fulfillment & Logistics",
        status: "available",
        skill_level: "senior"
      },
      department_name: "Order Fulfillment & Logistics",
      status: "resolved",
      priority: "NORMAL",
      is_transferred: false,
      created_at: new Date(Date.now() - 15 * 60000).toISOString(),
      messages: [
        {
          id: 201,
          conversation_id: 2,
          sender_type: "customer",
          content: "What are your delivery times?",
          created_at: new Date(Date.now() - 15 * 60000).toISOString(),
          ai_analysis: {
            intent: "Delivery Information",
            sentiment: "Neutral",
            sentiment_score: 0.85,
            emotion: "Calm",
            topic: "Shipping",
            language: "English",
            stress_score: 15,
            communication_style: "Calm"
          }
        },
        {
          id: 202,
          conversation_id: 2,
          sender_type: "assistant",
          content: "Standard delivery usually takes 3–5 business days. Express shipping is delivered within 1–2 business days. If you share your order number, I can check the exact status of your specific order.",
          created_at: new Date(Date.now() - 14 * 60000).toISOString()
        }
      ],
      latest_coaching: null,
      full_context: {
        repeated_issue: { is_repeated_issue: false, issue_type: "None" },
        sla_info: { status: "Resolved", first_response_target_minutes: 120, resolution_target_minutes: 720 },
        escalation_info: { escalation_recommended: false }
      }
    },
    {
      id: 3,
      customer: {
        id: 3,
        name: "John Smith",
        email: "john.s@example.com",
        phone: "+1 (555) 345-6789",
        tier: "Standard",
        badge: "New Customer",
        total_contacts: 2,
        unresolved_issues: 1,
        current_stress_score: 78,
        predicted_style: "Direct",
        memories: []
      },
      agent: {
        id: 1,
        name: "Sarah Jenkins",
        email: "sarah.j@support.com",
        department_name: "Billing & Payments",
        status: "available",
        skill_level: "senior"
      },
      department_name: "Billing & Payments",
      status: "active",
      priority: "HIGH",
      is_transferred: false,
      created_at: new Date(Date.now() - 30 * 60000).toISOString(),
      messages: [
        {
          id: 301,
          conversation_id: 3,
          sender_type: "customer",
          content: "I've been charged twice and I need a refund immediately.",
          created_at: new Date(Date.now() - 30 * 60000).toISOString(),
          ai_analysis: {
            intent: "Billing & Payment",
            sentiment: "Negative",
            sentiment_score: 0.88,
            emotion: "Anger",
            topic: "Refund",
            language: "English",
            stress_score: 78,
            communication_style: "Direct"
          }
        }
      ],
      latest_coaching: {
        warning: "⚠️ HIGH STRESS ALERT (78/100): Customer reported potential duplicate charge. De-escalation & transaction verification protocol required.",
        is_repeated_issue: false,
        issue_type: "Billing Dispute",
        recommended_actions: [
          "Validate customer concern regarding the unexpected charge.",
          "Verify both transactions in Billing Gateway before discussing refund eligibility.",
          "Avoid promising immediate bank release before confirming duplicate batch ID.",
          "Provide concrete dispute ticket reference."
        ],
        empathy_guidance: "Direct & High Stress: Acknowledge financial distress immediately with professional assurance.",
        suggested_response: "I understand your concern regarding the duplicate charge and I apologize for the inconvenience. Let me review both transaction records right now so we can initiate a refund if verified.",
        escalation_required: false
      },
      full_context: {
        repeated_issue: { is_repeated_issue: false, issue_type: "None" },
        sla_info: { status: "On Track", first_response_target_minutes: 30, resolution_target_minutes: 240 },
        escalation_info: { escalation_recommended: false }
      }
    }
  ];
}

export async function fetchSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      return await res.json();
    }
  } catch (e) {
    console.warn("Could not reach health endpoint:", e);
  }
  return null;
}

export async function fetchConfiguredModel() {
  try {
    const res = await fetch(`${API_BASE}/config/model`);
    if (res.ok) {
      const data = await res.json();
      if (data.model) return data.model;
    }
    const healthRes = await fetch(`${API_BASE}/health`);
    if (healthRes.ok) {
      const hData = await healthRes.json();
      if (hData.gemini_model) return hData.gemini_model;
    }
  } catch (e) {
    console.warn("Could not fetch configured model:", e);
  }
  return 'gemini-3.5-flash';
}

