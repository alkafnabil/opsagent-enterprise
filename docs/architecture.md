# SYSTEM ARCHITECTURE
## OpsAgent: AI Operational Assistant

Dokumen ini mendokumentasikan arsitektur sistem monorepo, aliran data antarkomponen, tata kelola keamanan *guardrails*, dan pola orkestrasi agent.

---

### 1. HIGH-LEVEL SYSTEM TOPOLOGY

```mermaid
graph TD
    User["User (Staff / Manager)\nReact + Vite + Tailwind"] -->|SSE & REST HTTP| API["FastAPI Gateway\n(backend/app/main.py)"]
    
    subgraph Guardrails & Interceptors
        API --> GuardrailCheck["Guardrails Engine\n- PII Masking\n- Prompt Injection Detector\n- RBAC Scope Validator"]
    end

    GuardrailCheck -->|Valid Query| Router["Intent Router\n(Small Model: Llama-3.1-8B)"]
    GuardrailCheck -->|Blocked Query| DirectBlock["Rejection Response\n+ Audit Log Flag"]

    subgraph Agent Loop & Tool Execution
        Router --> AgentLoop["Orchestrator / ReAct Loop\n(LangGraph / Explicit State)"]
        
        AgentLoop -->|Intent: text-to-SQL| SQLTool["Tool: sql_query\n- AST Parser Validator\n- Read-Only User Connection"]
        AgentLoop -->|Intent: ERP Transaction| ERPTool["Tool: erp_api\n- Timeout & Retry Client\n- Pydantic v2 Schema"]
        AgentLoop -->|Intent: Calendar/Email| M365Tool["Tool: m365\n- Graph API / Mock Service"]
        AgentLoop -->|Intent: Policy/SOP| RAGTool["Tool: search_docs\n- ChromaDB / pgvector\n- Citations Generator"]
    end

    SQLTool --> ReadOnlyDB[("PostgreSQL DB (Read-Only)\nTables: stockpiles, barges, inventory")]
    ERPTool --> MockERP["Mock ERP Service\n(Port 8001: PO, Invoices)"]
    RAGTool --> VectorStore[("Vector Store\nSOP Documents Index")]

    subgraph Approval Flow
        ERPTool -->|Write Action: Create PO| ApprovalPending["HITL State: PENDING_APPROVAL\nEmit Approval Event via SSE"]
        ApprovalPending -->|Manager Confirm| ERPExecute["Execute PO Creation"]
    end

    AgentLoop --> Synthesis["Synthesis Model\n(Llama-3.3-70B)\nFinal Answer with Citations"]
    Synthesis --> StreamResp["Streaming Response Generator\nSSE Stream to React UI"]

    subgraph Observability
        AgentLoop --> AuditRecorder["Audit Logger\nWrite trace_id, tokens, latency, cost"]
        AuditRecorder --> AuditDB[("PostgreSQL\nTable: audit_log")]
    end
```

---

### 2. KOMPONEN MONOREPO & PORT ALLOCATION

| Komponen | Jalur Direktori | Port Default | Deskripsi & Peran |
|---|---|---|---|
| **PostgreSQL 16 + pgvector** | `data/seed_sql/` | `5432` | Basis data operasional batubara + pencatatan audit log & vector embeddings |
| **Mock ERP Service** | `mock_erp/` | `8001` | REST API independen simulasi ERP pengadaan, stok, tagihan, dan pengapalan |
| **Backend Service** | `backend/` | `8000` | FastAPI server yang menjalankan agent loop, tools, router, guardrails, & RAG |
| **Frontend UI** | `frontend/` | `5173` | React SPA dengan streaming SSE, live tool trace, dan modal approval |

---

### 3. KEAMANAN & GUARDRAIL ARCHITECTURE

```mermaid
sequenceDiagram
    autonumber
    actor User as User (Staff / Manager)
    participant UI as Frontend React
    participant API as FastAPI Backend
    participant Guard as Guardrails Engine
    participant Router as Fast Router (8B)
    participant Tool as Target Tool
    participant Synthesizer as LLM Synthesizer (70B)
    participant Audit as Postgres Audit Log

    User->>UI: Input pertanyaan ("Berapa sisa batubara di Jetty Palaran?")
    UI->>API: POST /api/v1/chat (SSE Stream)
    API->>Guard: Pre-execution validation (PII detection & Injection scan)
    
    alt Injeksi Terdeteksi / Pelanggaran Etika
        Guard-->>API: Reject dengan peringatan keamanan
        API->>Audit: Catat audit_log (guardrail_flagged=true)
        API-->>UI: Kirim pesan penolakan
    else Valid Query
        Guard->>Router: Route intent
        Router-->>API: Intent: sql_query
        API->>Tool: Eksekusi Tool sql_query (AST Check -> Read-Only DB)
        Tool-->>API: Data hasil query (Stockpile Palaran: 84.500 MT)
        API-->>UI: SSE Event: 'tool_trace' (latensi, SQL snippet)
        API->>Synthesizer: Sintesis respons final dengan data tool
        Synthesizer-->>API: Token streaming
        API-->>UI: SSE Event: 'token' (teks streaming)
        API->>Audit: Rekam jejak lengkap (trace_id, tokens, latency, cost)
    end
```

---

### 4. STRUKTUR DATA STATE AGENT (EXPLICIT REACTION STATE)
Agent menggunakan siklus state yang eksplisit:
```python
class AgentState(BaseModel):
    trace_id: str
    user_id: str
    user_role: str  # 'staff' | 'manager'
    user_query: str
    cleaned_query: str
    intent: Optional[str] = None
    tool_calls: list[ToolCall] = []
    tool_results: list[ToolResult] = []
    pending_approval: Optional[ApprovalRequest] = None
    citations: list[Citation] = []
    final_response: Optional[str] = None
    metrics: PerformanceMetrics
```
Pola state eksplisit ini memastikan setiap langkah dapat diaudit, diinterupsi saat membutuhkan *human approval*, dan dapat dimonitor secara transparan di panel *Tool Trace* frontend.
