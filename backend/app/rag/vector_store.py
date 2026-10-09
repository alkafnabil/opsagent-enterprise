from __future__ import annotations
import os
import math
import logging
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from .models import DocumentChunk, SearchResult, Citation
from .embeddings import BaseEmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class BaseVectorStore(ABC):
    @abstractmethod
    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: Optional[float] = None,
        doc_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        pass

    @abstractmethod
    def count(self) -> int:
        pass

    @abstractmethod
    def clear(self) -> None:
        pass

    @abstractmethod
    def get_document_names(self) -> List[str]:
        pass


class ChromaVectorStore(BaseVectorStore):
    """
    ChromaDB-backed vector store.
    Directly injects embeddings to avoid any remote model download overhead.
    """

    def __init__(
        self,
        collection_name: str = "sop_documents",
        persist_directory: Optional[str] = None,
        embedding_service: Optional[BaseEmbeddingService] = None,
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIR
        self.embedding_service = embedding_service or get_embedding_service()

        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )

        # Create or get collection with cosine space
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[DocumentChunk]) -> int:
        if not chunks:
            return 0

        ids = [c.chunk_id for c in chunks]
        texts = [c.content for c in chunks]
        embeddings = self.embedding_service.embed_batch(texts)
        metadatas = [
            {
                "doc_file_name": c.doc_file_name,
                "doc_code": c.doc_code,
                "doc_title": c.doc_title,
                "page_number": c.page_number,
                "section_title": c.section_title,
                "token_count": c.token_count,
            }
            for c in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: Optional[float] = None,
        doc_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        total_in_db = self.collection.count()
        if total_in_db == 0:
            return []

        query_embedding = self.embedding_service.embed_text(query)
        where_filter = {"doc_code": doc_filter} if doc_filter else None

        actual_k = min(top_k, total_in_db)
        response = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        results: List[SearchResult] = []
        if not response or not response["ids"] or not response["ids"][0]:
            return results

        ids = response["ids"][0]
        documents = response["documents"][0]
        metadatas = response["metadatas"][0]
        distances = response["distances"][0]

        for chunk_id, doc_text, meta, distance in zip(ids, documents, metadatas, distances):
            # Chroma cosine distance: distance = 1 - cosine_similarity
            # Therefore similarity = 1 - distance
            similarity = max(0.0, min(1.0, 1.0 - distance))

            if score_threshold is not None and similarity < score_threshold:
                continue

            doc_code = meta.get("doc_code", "SOP")
            page_num = meta.get("page_number", 1)
            section_title = meta.get("section_title", "General")
            doc_file_name = meta.get("doc_file_name", "")
            doc_title = meta.get("doc_title", "")
            token_count = meta.get("token_count", len(doc_text.split()))

            citation = Citation(
                source=doc_code,
                page=page_num,
                section=section_title,
                citation_text=f"[{doc_code}: Halaman {page_num}, {section_title}]",
            )

            chunk = DocumentChunk(
                chunk_id=chunk_id,
                doc_file_name=doc_file_name,
                doc_code=doc_code,
                doc_title=doc_title,
                page_number=page_num,
                section_title=section_title,
                content=doc_text,
                token_count=token_count,
            )

            results.append(
                SearchResult(
                    chunk=chunk,
                    similarity_score=round(similarity, 4),
                    citation=citation,
                )
            )

        # Sort descending by similarity
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results

    def count(self) -> int:
        return self.collection.count()

    def clear(self) -> None:
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def get_document_names(self) -> List[str]:
        if self.collection.count() == 0:
            return []
        data = self.collection.get(include=["metadatas"])
        docs = set()
        for meta in data.get("metadatas", []):
            if "doc_file_name" in meta:
                docs.add(meta["doc_file_name"])
        return sorted(list(docs))


_global_vector_store: Optional[ChromaVectorStore] = None


def get_vector_store(embedding_service: Optional[BaseEmbeddingService] = None) -> BaseVectorStore:
    global _global_vector_store
    if _global_vector_store is None:
        _global_vector_store = ChromaVectorStore(
            collection_name="opsagent_sop_store",
            embedding_service=embedding_service,
        )
    return _global_vector_store
