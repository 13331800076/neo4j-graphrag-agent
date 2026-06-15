import pytest
from graphrag_agent.ingestion.document import Document
from graphrag_agent.retrieval.chunker import Chunker
from graphrag_agent.retrieval.embedder import Embedder
from graphrag_agent.retrieval.vector_store import VectorStore


def test_chunker_splits_document():
    doc = Document(
        doc_id="test",
        title="Test",
        source="/tmp/test.txt",
        text="Hello world " * 100,
    )
    chunker = Chunker(chunk_size=50, overlap=10)
    chunks = chunker.chunk(doc)
    assert len(chunks) > 1
    assert chunks[0].metadata["parent_doc_id"] == "test"
    assert chunks[0].text in doc.text


def test_embedder_produces_vectors():
    embedder = Embedder()
    vecs = embedder.encode(["hello world", "procurement module"])
    assert vecs.shape == (2, 384)


def test_vector_store_search():
    embedder = Embedder()
    store = VectorStore(embedder)
    docs = [
        Document(doc_id="d1", title="Procurement", source="a.md", text="Procurement handles purchase orders."),
        Document(doc_id="d2", title="Inventory", source="b.md", text="Inventory manages stock levels."),
    ]
    store.add_documents(docs)
    results = store.search("purchase orders", top_k=2)
    assert len(results) > 0
    assert results[0].chunk_id == "d1"
    assert 0.0 <= results[0].score <= 1.0
