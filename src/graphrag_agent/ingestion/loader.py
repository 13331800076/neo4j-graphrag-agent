import json
from pathlib import Path
from typing import List, Union
from .document import Document


class DocumentLoader:
    def __init__(self, raw_docs_dir: Union[str, Path]):
        self.raw_docs_dir = Path(raw_docs_dir)

    def load_all(self) -> List[Document]:
        documents = []
        for path in sorted(self.raw_docs_dir.rglob("*")):
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}:
                doc = self._load_file(path)
                if doc:
                    documents.append(doc)
        return documents

    def _load_file(self, path: Path) -> Document:
        suffix = path.suffix.lower()
        if suffix == ".json":
            return self._load_json(path)
        return self._load_text(path)

    def _load_text(self, path: Path) -> Document:
        text = path.read_text(encoding="utf-8")
        title = path.stem.replace("_", " ").title()
        return Document(
            doc_id=path.stem,
            title=title,
            source=str(path),
            text=text,
            metadata={"type": path.suffix.lower()},
        )

    def _load_json(self, path: Path) -> Document:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return Document(
                doc_id=data.get("id", path.stem),
                title=data.get("title", path.stem),
                source=str(path),
                text=data.get("text", ""),
                metadata=data.get("metadata", {}),
            )
        if isinstance(data, list) and data:
            text = "\n".join(str(item) for item in data)
            return Document(
                doc_id=path.stem,
                title=path.stem,
                source=str(path),
                text=text,
                metadata={"type": ".json", "items": len(data)},
            )
        return None
