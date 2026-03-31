---
name: ai-chatbot-portal
description: "Project spec context for AI Chatbot Portal (OneChat / ระบบสนทนาอัจฉริยะกลาง) — a Thai government One-Stop-Service AI chatbot portal. Use this skill when working on any feature, API, UI, or backend logic for this project."
---

# AI Chatbot Portal — Project Spec

## Project Overview
- **Name:** AI Chatbot Portal (OneChat / ระบบสนทนาอัจฉริยะกลาง)
- **Client:** Institute for Good Governance Promotion (สถาบัน ก.พ.ร.), Future Government Project
- **Duration:** Nov 2025 – Aug 2026 (10 months)
- **Goal:** One-Stop-Service AI portal — citizens ask one question, get answers aggregated from multiple Thai government agencies

---

## System Architecture

```
User → Chatbot Portal Web UI (React)
         → AI Agent Orchestrator (Agentic AI / Supabase Edge Functions)
              ├── Keyword analysis → select agencies
              ├── Protocol Adapters → parallel calls to agencies
              │    ├── MCP (Model Context Protocol)
              │    ├── A2A (Agent-to-Agent Protocol)
              │    └── REST API
              ├── Retrieve response_schema from DB
              └── LLMs (synthesize Markdown answer with citations)
         → Final Response to User
```

---

## API Spec

### Endpoint
- **POST** `/ai-chat`
- **Base URL:** `https://zmhfizjnmrukgapeqqyi.supabase.co/functions/v1`
- **Auth:** `Authorization: Bearer {SUPABASE_ANON_KEY}`

### ChatRequest
```typescript
{
  query: string                        // required — user question
  conversation_id?: uuid               // for multi-turn
  conversation_history?: Array<{       // prior messages for context
    role: "user" | "assistant"
    content: string
  }>
  target_agencies?: Array<"fda" | "revenue" | "dopa" | "land">  // skip keyword detection
  options?: {
    language?: "th" | "en"            // default: "th"
    model?: string                    // default: "google/gemini-3-flash-preview"
    include_agent_steps?: boolean     // default: true
    max_agencies?: number             // 1-10, default: 4
    timeout_ms?: number               // 1000-30000, default: 10000
  }
}
```

### ChatResponse
```typescript
{
  success: boolean
  conversation_id: uuid
  responseTime: number                 // ms
  data: {
    answer: string                     // Markdown
    references: Array<{
      agency: string
      title: string
      url: string
    }>
    agentSteps: Array<{
      icon: string
      label: string
      status: "done" | "pending" | "error"
    }>
    agencies: Array<{
      id: "fda" | "revenue" | "dopa" | "land"
      name: string
      icon: string
    }>
    confidence: number                 // 0–1
  }
}
```

### Error Response
```typescript
{ success: false, error: string }
// 400 — missing query
// 500 — internal error
```

---

## Orchestrator Flow

1. Receive `query` from client
2. Analyze keywords → select agencies (or use explicit `target_agencies`)
3. Call agency endpoints in **parallel**
4. Fetch `response_schema` from DB → build Schema Guide for LLM
5. Send all retrieved data + question to LLM → synthesize Markdown answer
6. Return `answer`, `references`, `agentSteps`, `confidence`

---

## Pilot Agencies

| ID       | Thai Name                        | Domain                           | Endpoint |
|----------|----------------------------------|----------------------------------|----------|
| `dopa`   | กรมการปกครอง                   | Civil registration, ID cards     | `http://203.154.130.166/dopa/chat` |
| `land`   | กรมที่ดิน                       | Land titles, property            | `http://203.154.130.166/dol/chat` |
| `fda`    | สำนักงานคณะกรรมการอาหารและยา  | Food, drug, cosmetics            | TBD |
| `revenue`| กรมสรรพากร                     | Tax                              | TBD |

Agency endpoint payload format:
```json
{
  "session_id": "",
  "query": "{user question}"
}
```

---

## MCP Server Spec

- **GET /sse** — SSE transport (`Accept: text/event-stream`)
  - Server generates session_id and emits it via stream
  - Do NOT require `session_id` as query param upfront
- **POST /messages?sessionId=...** — send commands (`list_tools`, `list_resources`, etc.)
- **Resource URI:** `agencies://list` → returns agency catalog JSON

Agency catalog response shape:
```json
{
  "agencies": [
    {
      "name": "กรมการปกครอง",
      "description": "ระบบตรวจสอบข้อมูลทะเบียนราษฎร์ บัตรประชาชน และงานปกครอง",
      "endpoint_url": "http://203.154.130.166/dopa/chat",
      "expected_payload": { "session_id": "", "query": "{user question}" }
    }
  ],
  "total": 2
}
```

Field notes:
- `name` — unique agency name (AI Agent uses this for routing)
- `description` — detailed scope; **AI Agent reads this to decide which agencies to query**
- `endpoint_url` — REST API endpoint for HTTP POST
- `expected_payload` — JSON body structure the agency expects

---

## AI Agent Orchestrator Requirements

| Capability | Detail |
|---|---|
| **Reasoning** | Analyze query, plan, decide which agencies to route to |
| **Autonomous retrieval** | Search & aggregate info across agencies without pre-specified sources |
| **Evaluation** | Validate quality of retrieved data; retry if insufficient |
| **LLM synthesis** | Produce Markdown answer with citations via LLM |

---

## UI Requirements

| Feature | Detail |
|---|---|
| Chat interface | Natural, conversational; display multi-source results in readable format |
| Citations | Show source reference per answer section |
| Agent steps | Show real-time steps (icon + label + status) |
| Responsive | Desktop + mobile |
| Accessibility | Usable without technical knowledge |
| Extra features | Chat history, suggested questions, suggested prompts |

---

## Protocol Adapters

Three supported protocols:
- **MCP** — AI Agent accesses agency tools/data stores securely
- **A2A** — Multi-agent communication; supports Client and Remote modes
- **REST API** — Fallback for agencies not supporting MCP/A2A

Standard concerns: Authentication, Authorization, Data Format Standardization, Error Handling.

---

## Risk Mitigations (relevant to code)

| Risk | Code-level Mitigation |
|------|----------------------|
| Data staleness | Validate freshness; alert on stale data in AI Agent |
| Performance/Latency | Parallel agency calls; timeout per agency (`timeout_ms`) |
| PDPA / Security | PDPA filter, Guardrails on responses, Audit Log |
| Prompt Injection | Guardrails layer before response generation |
| Cross-agency data conflict | AI Agent evaluation step; flag conflicting data |
| User adoption | Clear UI, citation display, suggested questions |

---

## Tech Stack (inferred from codebase)

- **Frontend:** React + TypeScript + Vite + Tailwind CSS
- **Backend:** Supabase Edge Functions (Deno/TypeScript)
- **Database:** Supabase (PostgreSQL)
- **LLM:** Google Gemini (default: `google/gemini-3-flash-preview`)
- **Protocol:** MCP, A2A, REST
- **Containerization:** Docker + docker-compose
- **Proxy:** Nginx
