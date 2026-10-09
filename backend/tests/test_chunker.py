import pytest
from app.rag.chunker import RecursiveTokenChunker


def test_chunker_metadata_and_pages_extraction():
    chunker = RecursiveTokenChunker(target_min_tokens=100, target_max_tokens=300, overlap_tokens=30)
    sample_sop = """# STANDAR OPERASIONAL PROSEDUR
## PT NUSANTARA COAL OPERATIONS
**Nomor Dokumen:** SOP-OPS-001
**Revisi:** 03
### JUDUL: PROSEDUR BONGKAR MUAT TONGKANG

#### 1. TUJUAN
Memastikan proses pemuatan batubara berjalan aman dan lancar.

---
<!-- Page Break: Halaman 2 -->

#### 4. PELAKSANAAN PEMUATAN
Pemuatan dilakukan secara bertahap menggunakan conveyor loader. Kecepatan standar 1000 MT per jam.
Jika terjadi hujan lebat di atas 20 mm/jam, pemuatan wajib dihentikan sementara.
"""
    chunks = chunker.chunk_document(sample_sop, "SOP-OPS-001_Bongkar_Muat_Tongkang_Jetty.md")
    
    assert len(chunks) >= 2
    assert chunks[0].doc_code == "SOP-OPS-001"
    assert chunks[0].page_number == 1
    assert "TUJUAN" in chunks[0].section_title or "Pengantar" in chunks[0].section_title
    
    # Check page 2 chunk
    page_2_chunk = next(c for c in chunks if c.page_number == 2)
    assert page_2_chunk.doc_code == "SOP-OPS-001"
    assert "PELAKSANAAN PEMUATAN" in page_2_chunk.section_title
    assert "hujan lebat" in page_2_chunk.content


def test_chunker_token_counting_and_overlap():
    chunker = RecursiveTokenChunker(target_min_tokens=50, target_max_tokens=100, overlap_tokens=25)
    
    # Generate long repeating paragraph
    long_body = "Batubara kalori tinggi disimpan di stockpile Kalimantan Timur dengan pemadatan bulldozer. " * 30
    md = f"""**Nomor Dokumen:** SOP-OPS-002
### JUDUL: MITIGASI KEBAKARAN
#### 1. PROSEDUR
{long_body}
"""
    chunks = chunker.chunk_document(md, "SOP-OPS-002.md")
    
    assert len(chunks) > 1
    for c in chunks:
        assert c.token_count <= 150
        assert c.doc_code == "SOP-OPS-002"
