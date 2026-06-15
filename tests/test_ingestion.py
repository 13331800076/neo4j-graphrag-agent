from pathlib import Path
from graphrag_agent.ingestion.loader import DocumentLoader
from graphrag_agent.ingestion.document import Document


def test_load_text_document():
    loader = DocumentLoader("tests/fixtures")
    docs = loader.load_all()
    assert len(docs) >= 1
    doc = docs[0]
    assert isinstance(doc, Document)
    assert doc.title == "Sample Procurement"
    assert "procurement" in doc.text.lower()
    assert doc.source.endswith(".md")


def test_document_model():
    doc = Document(
        doc_id="test_001",
        title="Test Doc",
        source="/tmp/test.md",
        text="Hello world",
        metadata={"author": "test"},
    )
    assert doc.doc_id == "test_001"
    assert doc.metadata["author"] == "test"
