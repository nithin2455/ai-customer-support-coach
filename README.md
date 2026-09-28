# AI-Powered Customer Support Platform with Real-Time Agent Coaching

An enterprise-grade customer support platform that augments human agents in real time. Built with a **Human-in-the-Loop** architecture, the platform combines a hybrid customer response engine (deterministic rules, database entity lookups, and Google Gemini LLM reasoning) with real-time NLP analysis, customer stress scoring, contextual interaction memory, smart routing, dynamic SLA tracking, and an operational administrative dashboard.

---

## 🎯 Architecture & Philosophy

The core philosophy of this platform is **human augmentation, not human replacement**:
- **Automated Self-Service**: Common business inquiries (delivery policies, return windows, order status lookups) are resolved instantly via deterministic rules and database lookups.
- **Strict Guardrails**: Sensitive financial requests (refunds, duplicate charges), manager escalations, fraud/security issues, and high-stress customers are immediately handed off to human specialists.
- **Real-Time Agent Coaching**: When an inquiry reaches a human agent, the platform provides real-time coaching recommendations, empathy guidance, and suggested responses. The agent always retains full control to **[Use suggestion]**, **[Edit in box]**, or **[Ignore]**.
- **Customer Privacy**: Internal operational telemetry (stress scores, sentiment analysis, intent tags, coaching suggestions) is strictly restricted to agent and admin workspaces and is never exposed to the customer portal.

```
Customer Message
       │
       ▼
[Response Engine Priority]
  ├─ 1. Deterministic Business Rules ──────► Instant Verified Policy Answer (Auto-resolved)
  ├─ 2. Sensitive / Financial / Escalation ─► Immediate Human Specialist Handoff
  ├─ 3. Database Entity Lookup (Order #) ──► Verified Database Tracking Answer (Auto-resolved)
  └─ 4. General / Unknown Safe Query ──────► Google Gemini (google-genai SDK)
                                                ├─ Success ──► Helpful AI Answer
                                                └─ Quota/Offline ──► Reassuring Human Handoff Fallback
       │
       ▼ (If routed to Agent Queue)
[Context & Real-Time Coaching Pipeline]
  ├─ Customer Stress Score (0–100) & Communication Style Analysis
  ├─ Persistent Memory (Past touchpoints, unresolved issues, previous agent continuity)
  ├─ Smart Routing & SLA Timer (On Track / At Risk / Breached)
  └─ AI Coaching Panel (Action items, empathy guidance, draft response)
       │
       ▼
[Human Agent Final Control]
  └─ Agent reviews, customizes, and submits verified resolution to customer
```

---

## 🛠 Technology Stack

### Backend
- **Language & Framework**: Python 3.10+, FastAPI (Asynchronous REST API)
- **Data Validation & Settings**: Pydantic v2 & Pydantic Settings
- **ORM & Database**: SQLAlchemy 2.0 with SQLite (zero-config local development) and PostgreSQL compatibility
- **Generative AI Integration**: Official Google Gemini SDK (`google-genai>=2.0.0`)
- **NLP Engine**: Hugging Face `transformers` (sentiment, emotion, intent classification with lightweight heuristic fallbacks)
- **Security & Auth**: OAuth2 Password Bearer with JWT tokens, bcrypt password hashing, role-based access control (RBAC), and strict customer data isolation
- **Testing**: Pytest with automated unit, integration, RBAC, isolation, and live LLM diagnostic test suites

### Frontend
- **Framework & Build**: React 18 with Vite
- **Styling**: Clean Light Enterprise Design System (Tailwind CSS, Slate/Indigo palette)
- **Icons**: Lucide React
- **Architecture**: Modular single-page app with role-based navigation (Customer Portal, 3-Column Agent Workspace, Support Analytics, Operations Admin Dashboard)

---

## 📋 Environment Configuration

Copy the example environment file and configure your settings:

```bash
# In backend/ directory or root project directory
cp backend/.env.example backend/.env
```

### Environment Variables Reference

| Variable | Default Value | Description |
|---|---|---|
| `PROJECT_NAME` | `"AI Customer Support Coaching System"` | Human-readable application title |
| `ENVIRONMENT` | `"development"` | Environment mode (`development` / `production`) |
| `DEBUG` | `True` | Debug mode for detailed logging and docs |
| `API_V1_STR` | `"/api/v1"` | Base prefix for REST API endpoints |
| `SECRET_KEY` | `your-secret-key-change-in-production` | Secret key for JWT signature generation |
| `DATABASE_URL` | `"sqlite:///./support_coach.db"` | Database connection string (SQLite or PostgreSQL) |
| `LLM_PROVIDER` | `"gemini"` | External LLM provider for general safe questions (`gemini`) |
| `GEMINI_API_KEY` | `""` | Google AI Studio API key (kept strictly backend-only) |
| `GEMINI_MODEL` | `"gemini-3.5-flash"` | Gemini model identifier (fallback to `gemini-3.6-flash`) |
| `USE_HF_LOCAL_MODELS` | `False` | Set `True` to load local transformer weights |
| `CORS_ORIGINS` | `"http://localhost:5173,http://localhost:3000"` | Allowed cross-origin frontend origins |

> [!IMPORTANT]
> The `GEMINI_API_KEY` is strictly backend-only. It is never logged, never returned in API responses, and never bundled into frontend builds.

---

## 🚀 Getting Started

### Prerequisites
- **Python**: 3.10 or higher
- **Node.js**: 18 or higher (with npm)

---

### Step 1: Backend Setup

1. Open a terminal and navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database and populate default seed data:
   ```bash
   python -m app.db.seed
   ```

5. Start the FastAPI development server:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

- **API Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

### Step 2: Frontend Setup

1. Open a second terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```

- **Application URL**: [http://localhost:5173](http://localhost:5173)

---

### Step 3: Production Build (Frontend)

To validate or build the static production bundle:
```bash
cd frontend
npm run build
```
Build output is generated in `frontend/dist/`.

---

## 👥 Default Evaluation Credentials

The platform seeds realistic enterprise accounts across all roles:

| Role | Name | Email | Password | Assigned View |
|---|---|---|---|---|
| **Senior Agent** | Sarah Jenkins | `sarah.j@support.com` | `Agent123!` | 3-Column Agent Workspace |
| **Agent** | Michael Brown | `michael.b@support.com` | `Agent123!` | 3-Column Agent Workspace |
| **Customer** | Alex Johnson | `alex.j@example.com` | `Customer123!` | Focused Customer Portal |
| **Customer** | Priya Kumar | `priya.k@example.com` | `Customer123!` | Focused Customer Portal |
| **Customer** | John Smith | `john.s@example.com` | `Customer123!` | Focused Customer Portal |
| **Administrator** | System Admin | `admin@company.com` | `Admin123!` | Operations Admin & Analytics |

> [!TIP]
> The login page includes a collapsible **"Evaluation Test Credentials"** drawer with 1-click credential filling for rapid evaluation. New customer accounts can also be registered at any time via the registration toggle.

---

---

## 🌐 Multilingual Support

The platform includes free, end-to-end multilingual customer support:

### Supported Languages
- **English**: `en` (`en-IN`)
- **Hindi** (हिन्दी): `hi` (`hi-IN`)
- **Tamil** (தமிழ்): `ta` (`ta-IN`)
- **Kannada** (ಕನ್ನಡ): `kn` (`kn-IN`)

### Multilingual Features
1. **Customer Language Selection**: Customers can select their preferred language from the centralized dropdown in the message composer.
2. **Language-Aware Hybrid Response Pipeline**:
   - Deterministic business rules (standard delivery, shipping carrier, return policy, refund policy, cancellation window, payment methods, order status lookups) respond directly in the customer's selected language.
   - Dynamic non-English inquiries are processed via zero-cost deterministic templates or localized through Google Gemini LLM reasoning.
   - Sensitive financial requests (refunds, transfers) and supervisor escalations in any language trigger immediate human handoff with localized reassurances.
3. **Agent Workspace Localization**:
   - The human agent interface remains primarily in English.
   - In non-English customer conversations, the agent sees a compact language indicator (e.g. `Language: Tamil`), the customer's original message, and an instant English translation.
   - The agent writes replies in English, which the system automatically translates into the customer's selected language upon submission while preserving the agent's original English copy for audit logs.

---

## 🎙 Voice Support

The platform provides client-side voice interaction using free, browser-native APIs:

- **Browser-Based Speech Recognition**: Uses `window.SpeechRecognition` or `window.webkitSpeechRecognition` with interim transcript streaming, automatic cleanup, and explicit user editing before sending.
- **Browser-Based Text-to-Speech**: Uses `window.speechSynthesis` with `SpeechSynthesisUtterance` to read assistant responses aloud in the customer's locale.
- **Zero OpenAI / Zero Paid Voice APIs**:
  - NO OpenAI API dependencies
  - NO `OPENAI_API_KEY`
  - NO OpenAI Whisper API
  - NO OpenAI TTS API
  - Zero external paid voice or transcription services. Customer audio stays local to the user's browser.

### ⚠️ Important Limitations
- **Browser & OS Dependence**: Speech recognition and voice synthesis rely directly on the client's operating system and browser capabilities (such as Google Chrome, Microsoft Edge, or Safari).
- **Voice Pack Availability**: Availability of individual Indian-language text-to-speech voices (such as Tamil or Kannada) depends on the voices installed on the user's OS and browser. If a specific voice is not installed, the application gracefully notifies the customer without crashing or interrupting text communication.

---

## 🧪 Automated Testing & Verification

### Running Backend Automated Tests

Run the complete 106-test test suite using Pytest:

```bash
cd backend
pytest tests -v
```

**Test Coverage Summary (106 / 106 Passed, 100% Pass Rate)**:
- `test_multilingual_voice.py` (18 tests): Centralized language configuration, script detection, deterministic multilingual templates, English/Hindi/Tamil/Kannada response engine routing, sensitive refund handoff in Indic languages, agent response translation, and zero OpenAI verification.
- `test_llm_diagnostics.py` (13 tests): Key sanitization, mocked Gemini responses, error fallback handling, and rate limit resilience.
- `test_phase8_response_engine.py` (14 tests): Response engine priority rules, order database lookup, refund human handoff, and message persistence.
- `test_phase9_auth_and_isolation.py` (22 tests): Registration, JWT authentication, role authorization, customer conversation isolation, and timezone awareness.
- `test_phase3.py` (6 tests): Customer memory profiles, interaction timelines, and repeated issue detection.
- `test_phase4.py` (4 tests): Stress-aware coaching, communication-style guidance, and agent feedback capture.
- `test_phase5.py` (7 tests): CSAT calculation, coaching effectiveness, and learning insights generation.
- `test_phase6.py` (9 tests): Smart routing, dynamic SLA calculation, escalation rules, and end-to-end integration.
- `test_phase7_workflow.py` (6 tests): End-to-end multi-turn customer, assistant, and agent workflows.

### Running Live End-to-End Verification

To verify the live application with live Gemini API requests, customer messaging, agent response delivery, and admin telemetry:

```bash
cd backend
python verify_final_e2e.py
```

---

## 🔒 Security & Data Privacy

1. **API Key Isolation**: `GEMINI_API_KEY` is loaded strictly by backend services from environment variables and is never transmitted to the browser or stored in databases.
2. **Customer Data Isolation**: Customers are strictly scoped to their own conversations and order histories through authenticated token claims. Any cross-customer access attempt returns `403 Forbidden`.
3. **No Financial Self-Service**: The AI assistant cannot execute balance adjustments, refunds, or financial transfers. All financial requests require verification and execution by authorized human specialists.
4. **Audit Logging & Continuous Learning**: Agent coaching feedback (accepted, edited, or ignored) is logged anonymously to generate closed-loop continuous improvement insights for support leadership.
5. **No Audio Cloud Storage**: Microphone audio is processed entirely locally within the browser; raw voice audio is not uploaded or stored on backend servers.
