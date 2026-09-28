# System Architecture & Component Design

## Overview

The AI-Powered Intelligent Customer Support System provides real-time coaching to human customer support agents. The system does **not** replace the human agent; it acts as an intelligent co-pilot during live customer interactions.

---

## Data Flow Diagram

```
+------------------+
| Customer Message |
+--------+---------+
         |
         v
+------------------+     1. Sentiment & Emotion Analysis
|  FastAPI Engine  |---> 2. Intent & Topic Classification
+--------+---------+     3. Stress Score Calculation (0-100)
         |               4. Customer History & Memory Retrieval
         v               5. Communication-Style Prediction
+------------------+
| LLM Coach Engine |---> Generates Recommended Actions, Empathy Tips,
+--------+---------+     and Suggested Draft Response
         |
         v
+------------------+
|  Agent Dashboard |---> Displays Real-Time Coaching Panel
+--------+---------+     Agent accepts, edits, or ignores recommendation
         |
         v
+------------------+
| Final Agent Resp |---> Sent to Customer
+------------------+
```

---

## Core Modules

### 1. NLP Analysis Engine (`backend/app/ai/nlp_analyzer.py`)
- Analyzes incoming messages for Sentiment (Negative, Neutral, Positive), Emotion (Frustration, Confusion, Satisfaction, Anger), and Intent (Order Issue, Billing, Technical, General Inquiry).
- Uses Hugging Face `transformers` zero-shot & classification pipelines or fast heuristic fallback for high performance.

### 2. Stress Scoring Service (`backend/app/services/stress_service.py`)
Calculates a 0-100 Customer Stress Score based on:
- Negative sentiment weight (0 to +40)
- High-frustration emotion markers (0 to +25)
- Unresolved ticket count & recent contact frequency (0 to +25)
- Escalation trigger phrases ("waiting for a week", "unacceptable", "supervisor") (0 to +10)

Score Levels:
- **0 - 39**: LOW (Green)
- **40 - 69**: MEDIUM (Yellow)
- **70 - 100**: HIGH / CRITICAL (Red)

### 3. Customer Memory (`backend/app/services/memory_service.py`)
Stores historical touchpoints, previous issues, sentiment trends, and past resolutions. Automatically surfaces context to the agent so customers never repeat themselves.

### 4. Communication Style Engine (`backend/app/services/style_service.py`)
Surfaces behavioral recommendations:
- **Direct / Impatient**: Keep responses concise, action-oriented, skip fluff.
- **Detailed**: Provide clear step-by-step explanations and reference order numbers.
- **Calm / Friendly**: Maintain warm, friendly, professional tone.

### 5. Smart Routing (`backend/app/services/routing_service.py`)
Routes tickets based on department, stress level, and agent skill set. Sensitive or high-stress tickets are prioritized for human handling.

### 6. LLM Coaching Assistant (`backend/app/ai/llm_coach.py`)
Synthesizes NLP signals, customer memory, and conversation state into structured, actionable coaching output:
- Frustration warning
- Recommended actions checklist
- Empathy & tone guidance
- Suggested response template (1-click insert/edit)
