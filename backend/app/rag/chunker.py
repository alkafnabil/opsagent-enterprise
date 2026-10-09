from __future__ import annotations
import re
from typing import List, Tuple, Optional
import tiktoken
from .models import DocumentChunk


class RecursiveTokenChunker:
    """
    Recursive Token Chunker designed for Markdown SOPs.
    Target window: 500 - 800 tokens.
    Overlap: 80 tokens.
    Preserves document structure, exact page number, and section headings.
    """

    def __init__(
        self,
        target_min_tokens: int = 500,
        target_max_tokens: int = 800,
        overlap_tokens: int = 80,
    ):
        self.min_tokens = target_min_tokens
        self.max_tokens = target_max_tokens
        self.overlap_tokens = overlap_tokens

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        # Fast, robust cl100k_base token estimator (word tokens + punctuation)
        # Matches tiktoken closely without network download dependency
        return len(re.findall(r"\w+|[^\w\s]", text))

    def _extract_doc_metadata(self, text: str, file_name: str) -> Tuple[str, str]:
        """Extract doc_code and doc_title from markdown content."""
        code_match = re.search(r"\*\*Nomor Dokumen:\*\*\s*([A-Za-z0-9\-]+)", text)
        doc_code = code_match.group(1).strip() if code_match else file_name.split("_")[0]

        title_match = re.search(r"### JUDUL:\s*(.+)", text)
        if title_match:
            doc_title = title_match.group(1).strip()
        else:
            title_match2 = re.search(r"^# (.+)$", text, re.MULTILINE)
            doc_title = title_match2.group(1).strip() if title_match2 else file_name.replace(".md", "")

        return doc_code, doc_title

    def _split_into_pages(self, markdown_text: str) -> List[Tuple[int, str]]:
        """Splits markdown into (page_number, page_text) blocks."""
        page_pattern = re.compile(r"<!--\s*Page Break:\s*Halaman\s*(\d+)\s*-->", re.IGNORECASE)
        splits = page_pattern.split(markdown_text)

        pages: List[Tuple[int, str]] = []
        if len(splits) == 1:
            pages.append((1, splits[0].strip()))
        else:
            # First block before any page break marker is Page 1
            if splits[0].strip():
                pages.append((1, splits[0].strip()))
            
            # Remaining are pairs of (page_num_str, page_content)
            for i in range(1, len(splits), 2):
                p_num = int(splits[i])
                p_content = splits[i + 1].strip() if i + 1 < len(splits) else ""
                if p_content:
                    pages.append((p_num, p_content))

        return pages

    def _extract_sections(self, page_text: str) -> List[Tuple[str, str]]:
        """Splits a single page text by heading (#### or ###) while keeping section title."""
        heading_pattern = re.compile(r"^(#{2,4}\s+.+)$", re.MULTILINE)
        parts = heading_pattern.split(page_text)

        sections: List[Tuple[str, str]] = []
        current_title = "Umum / Pengantar"
        current_body = ""

        for part in parts:
            part = part.strip()
            if not part:
                continue
            if part.startswith("#"):
                if current_body:
                    sections.append((current_title, current_body.strip()))
                    current_body = ""
                current_title = part.lstrip("#").strip()
            else:
                current_body += "\n\n" + part if current_body else part

        if current_body:
            sections.append((current_title, current_body.strip()))

        return sections if sections else [("Umum", page_text)]

    def _split_long_text(self, text: str, section_title: str) -> List[str]:
        """Recursively split text that exceeds max_tokens with overlap_tokens."""
        tokens = self.count_tokens(text)
        if tokens <= self.max_tokens:
            return [text]

        # Split by paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_tokens = 0

        for para in paragraphs:
            para_tokens = self.count_tokens(para)
            if current_tokens + para_tokens <= self.max_tokens:
                current_chunk.append(para)
                current_tokens += para_tokens
            else:
                if current_chunk:
                    chunk_str = "\n\n".join(current_chunk)
                    chunks.append(chunk_str)
                    
                    # Create overlap using last paragraph(s) up to overlap_tokens
                    overlap_paras = []
                    overlap_tok = 0
                    for p in reversed(current_chunk):
                        p_t = self.count_tokens(p)
                        if overlap_tok + p_t <= self.overlap_tokens:
                            overlap_paras.insert(0, p)
                            overlap_tok += p_t
                        else:
                            break
                    current_chunk = overlap_paras + [para]
                    current_tokens = sum(self.count_tokens(p) for p in current_chunk)
                else:
                    # Single paragraph exceeds max_tokens; split by sentences
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    s_chunk: List[str] = []
                    s_tokens = 0
                    for s in sentences:
                        st = self.count_tokens(s)
                        if s_tokens + st <= self.max_tokens:
                            s_chunk.append(s)
                            s_tokens += st
                        else:
                            if s_chunk:
                                chunks.append(" ".join(s_chunk))
                            s_chunk = [s]
                            s_tokens = st
                    if s_chunk:
                        current_chunk = [" ".join(s_chunk)]
                        current_tokens = s_tokens

        if current_chunk:
            chunk_str = "\n\n".join(current_chunk)
            if not chunks or chunk_str != chunks[-1]:
                chunks.append(chunk_str)

        return chunks

    def chunk_document(self, markdown_text: str, file_name: str) -> List[DocumentChunk]:
        """
        Parses document and generates chunks with full citation metadata.
        Target size 500-800 tokens, 80 tokens overlap.
        """
        doc_code, doc_title = self._extract_doc_metadata(markdown_text, file_name)
        pages = self._split_into_pages(markdown_text)
        
        all_chunks: List[DocumentChunk] = []
        chunk_sequence = 1

        for page_num, page_content in pages:
            sections = self._extract_sections(page_content)
            
            # Accumulate small sections on same page until min_tokens or page end
            buffer_sections: List[Tuple[str, str]] = []
            buffer_tokens = 0

            for sec_title, sec_content in sections:
                sec_text = f"### {sec_title}\n\n{sec_content}"
                sec_tokens = self.count_tokens(sec_text)

                if sec_tokens > self.max_tokens:
                    # Flush previous buffer
                    if buffer_sections:
                        combined_content = "\n\n".join(
                            f"### {st}\n\n{sc}" for st, sc in buffer_sections
                        )
                        combined_title = " / ".join(st for st, _ in buffer_sections)
                        c_tokens = self.count_tokens(combined_content)
                        chunk_id = f"{doc_code}-P{page_num:02d}-C{chunk_sequence:02d}"
                        all_chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                doc_file_name=file_name,
                                doc_code=doc_code,
                                doc_title=doc_title,
                                page_number=page_num,
                                section_title=combined_title,
                                content=combined_content,
                                token_count=c_tokens,
                            )
                        )
                        chunk_sequence += 1
                        buffer_sections = []
                        buffer_tokens = 0

                    # Split this long section
                    sub_texts = self._split_long_text(sec_content, sec_title)
                    for idx, sub_text in enumerate(sub_texts):
                        content_with_header = f"### {sec_title} (Part {idx + 1})\n\n{sub_text}"
                        c_tokens = self.count_tokens(content_with_header)
                        chunk_id = f"{doc_code}-P{page_num:02d}-C{chunk_sequence:02d}"
                        all_chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                doc_file_name=file_name,
                                doc_code=doc_code,
                                doc_title=doc_title,
                                page_number=page_num,
                                section_title=sec_title,
                                content=content_with_header,
                                token_count=c_tokens,
                            )
                        )
                        chunk_sequence += 1
                else:
                    if buffer_tokens + sec_tokens > self.max_tokens:
                        # Flush current buffer
                        combined_content = "\n\n".join(
                            f"### {st}\n\n{sc}" for st, sc in buffer_sections
                        )
                        combined_title = " / ".join(st for st, _ in buffer_sections)
                        c_tokens = self.count_tokens(combined_content)
                        chunk_id = f"{doc_code}-P{page_num:02d}-C{chunk_sequence:02d}"
                        all_chunks.append(
                            DocumentChunk(
                                chunk_id=chunk_id,
                                doc_file_name=file_name,
                                doc_code=doc_code,
                                doc_title=doc_title,
                                page_number=page_num,
                                section_title=combined_title,
                                content=combined_content,
                                token_count=c_tokens,
                            )
                        )
                        chunk_sequence += 1
                        buffer_sections = [(sec_title, sec_content)]
                        buffer_tokens = sec_tokens
                    else:
                        buffer_sections.append((sec_title, sec_content))
                        buffer_tokens += sec_tokens

            # Flush remaining buffer on this page
            if buffer_sections:
                combined_content = "\n\n".join(
                    f"### {st}\n\n{sc}" for st, sc in buffer_sections
                )
                combined_title = " / ".join(st for st, _ in buffer_sections)
                c_tokens = self.count_tokens(combined_content)
                chunk_id = f"{doc_code}-P{page_num:02d}-C{chunk_sequence:02d}"
                all_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_file_name=file_name,
                        doc_code=doc_code,
                        doc_title=doc_title,
                        page_number=page_num,
                        section_title=combined_title,
                        content=combined_content,
                        token_count=c_tokens,
                    )
                )
                chunk_sequence += 1

        return all_chunks
