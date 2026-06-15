from typing import List
from graphrag_agent.ingestion.document import Document


class Chunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, document: Document) -> List[Document]:
        text = document.text
        chunks = []
        start = 0
        idx = 0
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            chunk_doc = Document(
                doc_id=f"{document.doc_id}_chunk_{idx}",
                title=f"{document.title} (chunk {idx})",
                source=document.source,
                text=chunk_text,
                metadata={
                    **document.metadata,
                    "parent_doc_id": document.doc_id,
                    "chunk_index": idx,
                    "start_char": start,
                    "end_char": end,
                },
            )
            chunks.append(chunk_doc)
            start += self.chunk_size - self.overlap
            idx += 1
        return chunks
