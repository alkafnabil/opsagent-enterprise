# OpsAgent: AI Asisten Operasional Internal (Distribusi Batubara)

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.2-646CFF?logo=vite)](https://vitejs.dev)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%2B%20pgvector-336791?logo=postgresql)](https://www.postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-orange)](https://www.trychroma.com)
[![Tests](https://img.shields.io/badge/Tests-51%2F51%20Passed-brightgreen)](backend/tests/)
[![Benchmark](https://img.shields.io/badge/Benchmark-100%25%20(40%2F40)-success)](eval/benchmark_report.md)

**OpsAgent** adalah AI agent asisten operasional internal *end-to-end* untuk perusahaan distribusi batubara (**PT Nusantara Coal Operations**). Sistem ini dibangun untuk menghubungkan seluruh silo operasional—mulai dari data relasional stockpile, sistem ERP pengadaan & faktur, jadwal logistik jetty Microsoft 365, hingga dokumen kepatuhan SOP internal.

Karyawan cukup bertanya dalam bahasa Indonesia sehari-hari. Agent secara otonom mengklasifikasikan kebutuhan pengguna, memilih *tool* yang relevan (SQL, Mock ERP, RAG, M365), memfilter input melalui lapisan *enterprise guardrails*, meminta persetujuan berjenjang (*Human-in-the-Loop*) untuk mutasi data sensitif, dan mengembalikan jawaban akurat yang dilengkapi sitasi resmi dokumen SOP serta jejak audit (*audit trail*) transparan.

---

## 🏛️ Arsitektur Sistem

OpsAgent mengimplementasikan pola **Two-Tier LLM Architecture** dengan pemisahan peran antara model klasifikasi berlatensi rendah (< 250 ms) dan model penalaran tinggi untuk sintesis operasional.

```mermaid
graph TD
    User["Karyawan (Staff / Manager)\nReact + Vite + Tailwind UI"] -->|SSE Stream & REST| Gateway["FastAPI API Gateway\n(Port 8000)"]
    
    subgraph Enterprise Guardrails
        Gateway --> Guardrails["Guardrail Engine\n1. Direct/Indirect Prompt Injection\n2. PII Masking (NIK, HP, Email)\n3. Role-Based Access Control (RBAC)"]
    end

    Guardrails -->|Blocked / Malicious| DirectRejection["Blokir & Catat Log Audit\n(Status: REJECTED)"]
    Guardrails -->|Safe Query| RouterTier["Tier 1: Intent Router (< 250ms)\nSmall Model (8B / Heuristic)"]

    subgraph Agent Loop & Tools
        RouterTier -->|Intent: Stock & Barges| SQLTool["Tool: sql_query\n- Read-Only User (opsagent_ro)\n- AST Parser (sqlparse)\n- Table Allowlist"]
        RouterTier -->|Intent: PO & Invoices| ERPTool["Tool: erp_api\n- Mock ERP Service (Port 8001)\n- Purchase Order, Invoice, Supplier"]
        RouterTier -->|Intent: SOP & Kebijakan| RAGTool["Tool: search_docs\n- ChromaDB / Vector Store\n- Multilingual Embeddings\n- Sitasi Bab & Halaman"]
        RouterTier -->|Intent: Jadwal & Memo| M365Tool["Tool: m365\n- Jetty Calendar & Draft Email"]
    end

    subgraph Human-in-the-Loop Approval
        ERPTool -->|Write Action: Create PO| ApprovalMgr["Approval Manager\nStatus: PENDING_APPROVAL\nEmit SSE Event -> UI Modal"]
        ApprovalMgr -->|Manager Decision| ERPExecute["Eksekusi Pembuatan PO"]
    end

    SQLTool --> Database[("PostgreSQL 16 DB\nStockpile, Tongkang, Produksi")]
    ERPTool --> MockERP["Mock ERP Service\n(FastAPI Port 8001)"]
    RAGTool --> SOPDocs[("Dokumen SOP Internal\nSOP-001 s.d. SOP-004")]

    AgentLoopFinal["Synthesis Model (Tier 2: 70B / LLM)\nSintesis Jawaban + Sitasi SOP"]
    SQLTool --> AgentLoopFinal
    ERPTool --> AgentLoopFinal
    RAGTool --> AgentLoopFinal
    M365Tool --> AgentLoopFinal

    AgentLoopFinal --> SSEStream["Streaming Generator (SSE)\nKirim Token, Tool Result, & Citations"]
    SSEStream --> User

    subgraph Full Observability
        Gateway --> AuditLogger["Audit Logger\nTrace ID, Latensi, Token, Biaya"]
        AuditLogger --> AuditTable[("Tabel audit_log")]
    end
```

---

## 📁 Struktur Monorepo

```text
OpsAgent/
├── backend/                       # OpsAgent Core API & Agent Loop
│   ├── app/
│   │   ├── agent/                 # Orchestrator, State Machine, Router, LLM Provider
│   │   ├── api/v1/endpoints/      # REST & SSE Endpoints (chat, approvals, docs, audit)
│   │   ├── core/                  # Database resilient pooling, Audit logger, Config
│   │   ├── guardrails/            # Injection detector, PII masker, RBAC, Approval manager
│   │   ├── models/                # SQLAlchemy models (AuditLog, Operational tables)
│   │   ├── rag/                   # Chunker (500-800 token), Embeddings, ChromaDB store
│   │   └── tools/                 # sql_query, erp_api, m365, search_docs, tool registry
│   ├── tests/                     # 51 Unit tests backend
│   ├── Dockerfile
│   └── requirements.txt
├── mock_erp/                      # Standalone Mock ERP Microservice (Port 8001)
│   ├── main.py                    # REST endpoints (inventory, PO, invoices, shipments)
│   ├── models.py                  # Pydantic v2 schemas
│   ├── database.py                # Thread-safe in-memory enterprise storage
│   ├── test_mock_erp.py           # Unit tests mock ERP
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                      # React UI (Vite + Tailwind CSS)
│   ├── src/
│   │   ├── components/            # Header, ToolTracePanel, ApprovalModal, CitationsCard
│   │   ├── App.jsx                # SSE Reader, Chat stream, State management
│   │   └── index.css              # Dark theme tokens, Coal color palette, Glassmorphism
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── data/
│   ├── seed_sql/                  # 01_init_schema.sql (DB & user read-only), 02_seed_data.sql
│   └── sop_docs/                  # SOP-001 (Bongkar Muat), SOP-002 (Panas/Kebakaran),
│                                  # SOP-003 (Matriks PO), SOP-004 (Toleransi Timbangan)
├── eval/                          # Benchmark Suite (Fase 6)
│   ├── golden_dataset.jsonl       # 40 Skenario operasional (SQL, ERP, RAG, Guardrails)
│   ├── runner.py                  # Eksekutor evaluasi otomatis multi-tier
│   └── benchmark_report.md        # Laporan metrik akurasi & latensi
├── docs/                          # Dokumentasi Portofolio
│   ├── PRD.md                     # Product Requirements Document
│   ├── architecture.md            # Spesifikasi arsitektur teknis & topologi
│   └── demo_script.md             # Naskah presentasi demo 5 menit
├── docker-compose.yml             # Orkestrasi 4 kontainer (DB, Mock ERP, Backend, Frontend)
├── .env.example                   # Template konfigurasi environment
└── README.md
```

---

## ⚡ Fitur Utama & Keunggulan Portofolio

### 1. Deterministic & Secure Tool Calling
- **`sql_query`:** Menjalankan query SQL dengan koneksi read-only user (`opsagent_ro`). Divalidasi oleh AST parser (`sqlparse`) yang membatasi statement hanya `SELECT`, mewajibkan allowlist 6 tabel operasional, dan otomatis menginjeksi batas `LIMIT 50`.
- **`erp_api`:** Klien REST dengan penanganan timeout, retry, dan validasi skema Pydantic v2 untuk modul pembelian, stok gudang, dan tagihan faktur.
- **`m365`:** Integrasi kalender jetty dan draft memo email dengan fallback mock otomatis.
- **`search_docs`:** Retrieval-Augmented Generation (RAG) atas 4 SOP resmi PT Nusantara Coal Operations dengan sitasi presisi (nama dokumen + nomor halaman + subbab).

### 2. Enterprise Guardrails & Kepatuhan
- **Prompt Injection Defense:** Mendeteksi serangan jailbreak langsung (*direct injection*) dan manipulasi yang disisipkan dalam dokumen (*indirect injection*) dengan skor risiko threshold 0.75.
- **PII Masking:** Sanitasi otomatis nomor NIK 16-digit (`317405******0001`), nomor HP Indonesia (`0812****5432`), dan email sebelum dikirim ke model atau dicatat ke log audit.
- **RBAC Policy:** Penegakan hak akses bertingkat: **Staff Operasional** (*Dimas Pratama*) vs **Operations Manager** (*Hendra Setiawan*). Limit kredit keuangan hanya dapat dilihat oleh Manager.

### 3. Human-in-the-Loop (HITL) Approval Flow
- Permintaan aksi tulis yang berdampak finansial (seperti penerbitan Purchase Order batubara) **tidak pernah dieksekusi secara langsung**.
- Agent mendaftarkan draft PO dengan status `PENDING`, memancarkan event `approval_required` melalui SSE stream, dan menampilkan modal persetujuan di UI.
- Staff tidak memiliki otoritas menyetujui (tombol terkunci), sedangkan Manager dapat meninjau tonase, supplier, nilai USD, menambahkan catatan verifikasi, dan memilih **Setujui (Approve)** atau **Tolak (Reject)**.

### 4. Observability Penuh & Audit Trail
- Setiap interaksi dicatat dengan `trace_id` unik ke tabel `audit_log`, mencakup: pengguna, peran, intent router, nama tool, argumen JSON, ringkasan output, status eksekusi, latensi per tahap (ms), jumlah token, dan estimasi biaya transaksi dalam USD.

---

## 📊 Hasil Evaluasi & Tolok Ukur Kinerja (Fase 6)

Sistem telah diuji secara komprehensif menggunakan **Golden Dataset 40 Kasus Uji** (`eval/golden_dataset.jsonl`) melalui script eksekusi otomatis `eval/runner.py`:

| Kategori Pengujian | Jumlah Kasus | Lolos (Pass) | Akurasi (%) | Target SLA |
| :--- | :---: | :---: | :---: | :---: |
| **SQL Data Query (`sql_query`)** | 10 | 10 | **100.0%** | ≥ 90.0% |
| **ERP Transactions & HITL (`erp_api`)** | 10 | 10 | **100.0%** | ≥ 90.0% |
| **RAG & SOP Citations (`search_docs`)** | 10 | 10 | **100.0%** | ≥ 90.0% |
| **Guardrails & Security (`guardrails`)** | 10 | 10 | **100.0%** | ≥ 95.0% |
| **TOTAL BENCHMARK OVERALL** | **40** | **40** | **100.0%** | **PASS (EXCEEDED)** |

### Profil Latensi Multi-Tier (Benchmark Terukur)
- **Tier 1 (Intent Router):** `p50 = 0.02 ms` | `p95 = 0.03 ms` *(Jauh di bawah target 250 ms)*.
- **Tier 2 (Tool Execution):** `p50 = 4.77 ms` | `p95 = 2,492 ms`.
- **Total End-to-End Latency:** `p50 = 2,501 ms` | `p95 = 10,271 ms`.
- **Konsumsi Biaya:** Rata-rata hanya `$0.00028 USD` per query.

---

## 🚀 Panduan Menjalankan Sistem

### Opsi A: Menjalankan via Docker Compose (Rekomendasi Produksi)

1. **Clone repository dan persiapkan environment:**
   ```bash
   cp .env.example .env
   ```
2. **Jalankan seluruh service:**
   ```bash
   docker compose up --build
   ```
3. **Akses antarmuka:**
   - **Frontend UI:** [http://localhost:5173](http://localhost:5173)
   - **Backend API & Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Mock ERP API & Docs:** [http://localhost:8001/docs](http://localhost:8001/docs)
   - **PostgreSQL Database:** `localhost:5432` (`opsagent_db`)

---

### Opsi B: Menjalankan Secara Lokal Tanpa Docker (Local Development)

Sistem dilengkapi **resilient database engine**: jika driver PostgreSQL lokal belum terpasang, sistem otomatis beralih ke SQLite fallback (`opsagent_dev.db`) tanpa memerlukan setup eksternal.

1. **Setup Backend & Mock ERP:**
   ```bash
   # Buat & aktifkan virtual environment (Python 3.11 atau 3.12)
   python -m venv venv
   source venv/bin/activate  # atau venv\Scripts\activate di Windows

   # Install dependencies
   pip install -r backend/requirements.txt
   pip install -r mock_erp/requirements.txt
   ```

2. **Jalankan Mock ERP Service (Terminal 1):**
   ```bash
   python -m uvicorn mock_erp.main:app --port 8001 --reload
   ```

3. **Jalankan Backend Service (Terminal 2):**
   ```bash
   python -m uvicorn backend.app.main:app --port 8000 --reload
   ```

4. **Jalankan Frontend React (Terminal 3):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Buka browser di [http://localhost:5173](http://localhost:5173).

---

## 🧪 Menjalankan Pengujian (Testing & Benchmark)

1. **Jalankan 51 Unit Tests (Pytest):**
   ```bash
   # Di Windows PowerShell:
   $env:PYTHONPATH="backend;.mock_erp"; python -m pytest backend/tests/ mock_erp/test_mock_erp.py

   # Di Linux / macOS:
   PYTHONPATH="backend:mock_erp" pytest backend/tests/ mock_erp/test_mock_erp.py
   ```
   *(Seluruh 51 test lulus dalam ~20 detik).*

2. **Jalankan Automated Benchmark (Golden Dataset 40 Kasus):**
   ```bash
   python eval/runner.py
   ```
   Hasil benchmark lengkap tersimpan di `eval/benchmark_report.md`.

---

## 📡 Referensi API Utama

| Method | Endpoint | Deskripsi |
| :--- | :--- | :--- |
| `POST` | `/api/v1/chat` | Streaming SSE endpoint (`router_step`, `tool_call`, `tool_result`, `approval_required`, `token`, `citations`, `done`) |
| `POST` | `/api/v1/chat/sync` | Synchronous endpoint agent loop (ideal untuk benchmark runner) |
| `GET` | `/api/v1/search-docs` | Semantic search RAG SOP dengan ekstraksi sitasi halaman |
| `POST` | `/api/v1/index-docs` | Re-indexing dokumen SOP internal ke ChromaDB |
| `GET` | `/api/v1/approvals` | Mengambil daftar pending approvals aksi tulis (PO) |
| `POST` | `/api/v1/approvals/{id}/decision` | Keputusan persetujuan HITL (`APPROVE` / `REJECT`) dengan validasi RBAC |
| `GET` | `/api/v1/audit-logs` | Mengambil riwayat log audit kepatuhan dan latensi |
| `GET` | `/health` | Healthcheck kesiapan backend database & tool registry |

---

## 🎬 Naskah Demo Portofolio
Untuk mempresentasikan sistem ini kepada manajemen atau tim rekruter, lihat panduan alur presentasi lengkap di [docs/demo_script.md](docs/demo_script.md).

---

## 📋 Status Pengerjaan (Semua Fase Selesai)
- [x] **Fase 1: Struktur Monorepo, Docker Compose, Seed Data SQL, & Mock ERP Microservice**
- [x] **Fase 2: Pipeline RAG, Chunker (500–800 token), Embeddings Multibahasa, & Sitasi Dokumen**
- [x] **Fase 3: Agent Orchestrator ReAct Loop, Tool Registry, Router 8B, & Audit Logger**
- [x] **Fase 4: Safety Guardrails, Prompt Injection Defense, PII Masker, RBAC, & HITL Approval**
- [x] **Fase 5: Frontend UI React 18 (Vite, Tailwind, SSE Streaming, Live Trace Panel, Approval Modal)**
- [x] **Fase 6: Evaluasi Golden Dataset 40 Kasus (100% Akurasi), Benchmark Latensi, & Dokumentasi Lengkap**

---

*Dikembangkan sebagai portofolio implementasi AI Agent operasional korporat tingkat enterprise.*
