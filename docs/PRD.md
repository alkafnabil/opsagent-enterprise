# PRODUCT REQUIREMENTS DOCUMENT (PRD)
## OpsAgent: AI Operational Assistant for Coal Distribution & Logistics
**Perusahaan:** PT Nusantara Coal Operations  
**Versi:** 1.0.0 (Fase 1 Foundation)  
**Status:** In Development  
**Target Pengguna:** Staff Operasional & Manager Distribusi Batubara  

---

### 1. LATAR BELAKANG & PROBLEM STATEMENT
Distribusi batubara melibatkan rantai pasok yang kompleks: jadwal sandar tongkang (*barge loading/discharge*), variasi kalori (*GAR 3800 s/d GAR 5000*), monitoring *self-combustion* di stockpile, ketaatan terhadap standar operasional maritim (SOP), serta penagihan invoice bernilai jutaan dolar.

**Masalah Saat Ini:**
1. **Data Terisolasi (Data Silo):** Data stok ada di PostgreSQL/database operasional, data PO dan Invoice ada di ERP SAP/Oracle terpisah, jadwal sandar ada di Outlook/M365, dan aturan mitigasi kebakaran ada di dokumen SOP PDF statis.
2. **Keterlambatan Pengambilan Keputusan:** Karyawan operasional membutuhkan waktu 15–45 menit untuk mencocokkan data antar sistem ketika tongkang tiba atau buyer komplain mengenai kualitas kalori.
3. **Risiko Kesalahan Aksi Tulis (Write Actions):** Tidak adanya pagar pembatas (*guardrails*) otomatis saat staf operasional membuat pesanan pembelian (Purchase Order) baru tanpa persetujuan berjenjang.
4. **Ketiadaan Jejak Audit AI:** Kurangnya auditabilitas atas jawaban asisten AI terdahulu, apakah data yang dikutip benar dan terverifikasi dari database riil atau halusinasi.

---

### 2. TUJUAN PRODUK (PRODUCT GOALS)
OpsAgent dibangun sebagai asisten AI cerdas berbahasa Indonesia yang:
1. Memahami pertanyaan operasional natural dalam Bahasa Indonesia.
2. Memilih *tool* yang tepat secara deterministik dan aman (SQL query read-only, REST API Mock ERP, Microsoft 365, atau RAG dokumen SOP).
3. Menyajikan jawaban akurat dengan **sitasi transparan** (nama file, nomor halaman/bab) dan **jejak pemanggilan tool (Tool Trace)** yang dapat diaudit secara *real-time*.
4. Mengamankan operasional melalui validasi RBAC, masking PII (NIK, nomor HP, email), deteksi *prompt injection*, serta alur *Human-in-the-loop (Approval)* untuk semua aksi tulis.

---

### 3. USER PERSONAS & ROLE-BASED ACCESS CONTROL (RBAC)

| Peran | Persona | Tanggung Jawab & Hak Akses | Batasan Akses |
|---|---|---|---|
| **Staff Operasional** | *Dimas (Jetty Officer)* | - Menanyakan status stok batubara & suhu stockpile.<br>- Menanyakan posisi tongkang & jadwal sandar.<br>- Mencari SOP penanganan insiden lapangan.<br>- **Membuat Draft PO (status DRAFT).** | - **Dilarang** menyetujui PO secara definitif.<br>- **Dilarang** melihat credit limit rahasia tanpa izin. |
| **Manager Operasional** | *Hendra (Operations Manager)* | - Seluruh akses Staff.<br>- Menyetujui/menolak Draft PO (*Action Approval*).<br>- Melihat evaluasi invoice macet (*overdue*) dan analisis audit log. | - Memiliki wewenang penuh untuk aksi modifikasi data. |

---

### 4. FITUR UTAMA & SPESIFIKASI TEKNIS

#### F1. Dual-Model Architecture & Intelligent Router
- **Router Model (Small & Fast, e.g. Llama-3.1-8B-instant):** Mengklasifikasikan intent pertanyaan pengguna (`sql_query`, `erp_api`, `m365`, `search_docs`, `out_of_scope`) dengan latensi ultra-rendah (< 250 ms).
- **Synthesis Model (High-Reasoning, e.g. Llama-3.3-70B-versatile):** Menyusun jawaban akhir yang komprehensif, santun, dan menyertakan sitasi serta rekomendasi operasional.

#### F2. Tools Integrations
1. **`sql_query`:**
   - Text-to-SQL untuk database operasional PostgreSQL.
   - Guardrail: Terkoneksi menggunakan database role read-only (`opsagent_ro`), hanya mengizinkan sintaks `SELECT`, membatasi tabel pada allowlist (`customers`, `stockpiles`, `coal_inventory`, `barges`, `barge_shipments`), otomatis menginjeksi `LIMIT 50`, dan divalidasi via AST parser (`sqlparse`) sebelum eksekusi.
2. **`erp_api`:**
   - REST API ke Mock ERP.
   - Endpoint: Inquiry stok, status PO, status Invoice pelanggan, status pengiriman tongkang.
   - Write Operation: Pembuatan PO selalu berstatus `DRAFT` dan memicu modal konfirmasi / approval.
3. **`m365`:**
   - Microsoft 365 (Graph API / Mock Mode via environment variable).
   - Fitur: Cek ketersediaan jadwal meeting koordinasi jetty, pembuatan event kalender, dan draft email notifikasi pengapalan.
4. **`search_docs` (RAG SOP Internal):**
   - Pencarian dokumen operasional (`SOP-OPS-001`, `SOP-OPS-002`, `SOP-PROC-003`, `SOP-FIN-004`).
   - Chunking recursive (500–800 token, overlap 80 token), model embedding multibahasa.
   - Menghasilkan sitasi wajib mencakup: Dokumen, Judul SOP, Nomor Halaman / Bagian.

#### F3. Security & Safety Guardrails
- **Prompt Injection Defense:** Deteksi injeksi instruksi jailbreak dari prompt pengguna maupun konten dokumen tidak tepercaya.
- **PII Masking:** Otomatis menyamarkan Nomor HP, NIK, dan email pribadi pada tampilan UI dan log permanen audit (`0812****2341`).
- **Scope Enforcement:** Penolakan halus dan terarah untuk pertanyaan di luar urusan operasional perusahaan (contoh: ramalan zodiak, politik, resep masakan).
- **Human-in-the-Loop Approval:** Interupsi state agent saat aksi mutasi terdeteksi hingga pengguna berwenang mengonfirmasi di UI.

#### F4. Observability & Audit Trail
- Setiap interaksi dicatat ke tabel `audit_log` dengan rincian:
  `trace_id`, `user_id`, `user_role`, `user_query`, `tool_name`, `tool_arguments`, `tool_result_summary`, `latency_ms`, `total_tokens`, `estimated_cost_usd`, `status`.

---

### 5. TARGET METRIK KINERJA & EVALUASI
- **Latency Target:** First-token streaming < 800 ms, Total response p50 < 2.0 s, p95 < 4.5 s.
- **Eval Golden Dataset:** 40 kasus uji mencakup ketepatan router, akurasi SQL, kebenaran RAG (*faithfulness & recall*), dan ketahanan guardrail.
