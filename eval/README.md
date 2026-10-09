# OPSAGENT EVALUATION SUITE

Direktori ini dipersiapkan untuk pengujian komprehensif sistem (Fase 6):
1. `golden_dataset.jsonl`: 40 kasus uji yang mencakup:
   - Tool selection accuracy (apakah router memilih tool yang benar)
   - SQL correctness (apakah query SQL yang dihasilkan sintaks & semantiknya benar)
   - RAG faithfulness & context recall (kebenaran sitasi dan kepatuhan SOP)
   - Guardrails & injection rejection (apakah prompt injection dan topik out-of-scope ditolak)
2. `runner.py`: Script eksekusi otomatis yang mengukur akurasi per kategori, latensi p50/p95, dan token cost.
3. `reports/`: Hasil evaluasi benchmarking antar model (Groq Llama 3.3 vs OpenAI GPT-4o-mini vs Anthropic Claude 3.5 Sonnet).
