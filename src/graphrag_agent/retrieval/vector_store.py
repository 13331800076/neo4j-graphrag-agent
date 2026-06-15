from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from pydantic import BaseModel
from graphrag_agent.ingestion.document import Document
from .embedder import Embedder


class SearchResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    source: str
    metadata: Dict[str, Any]


class VectorStore:
    def __init__(self, embedder: Embedder, dimension: int = 384):
        self.embedder = embedder
        self.dimension = dimension
        self.index = faiss.IndexFlatIP(dimension)
        self.documents: Dict[str, Document] = {}
        self.vectors: Dict[int, str] = {}

    def add_documents(self, documents: List[Document]):
        if not documents:
            return
        texts = [doc.text for doc in documents]
        vectors = self.embedder.encode(texts)
        faiss.normalize_L2(vectors)
        self.index.add(vectors)
        for i, doc in enumerate(documents):
            idx = len(self.documents)
            self.documents[doc.doc_id] = doc
            self.vectors[idx] = doc.doc_id

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        query_vec = self.embedder.encode_query(query).reshape(1, -1)
        faiss.normalize_L2(query_vec)
        scores, indices = self.index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            doc_id = self.vectors.get(int(idx))
            if doc_id and doc_id in self.documents:
                doc = self.documents[doc_id]
                results.append(SearchResult(
                    chunk_id=doc.doc_id,
                    text=doc.text,
                    score=float(score),
                    source=doc.source,
                    metadata=doc.metadata,
                ))
        return results

    def clear(self):
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = {}
        self.vectors = {}
