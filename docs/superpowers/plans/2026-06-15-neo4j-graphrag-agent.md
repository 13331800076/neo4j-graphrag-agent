# Neo4j GraphRAG Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a complete Neo4j GraphRAG Agent project with rule-based extraction, template text2cypher, FAISS vector retrieval, and a FastAPI backend — all runnable via Docker Compose without any LLM API key.

**Architecture:** Clean Python src-layout with independent modules (ingestion, ontology, extraction, graph, retrieval, text2cypher, agent). FastAPI serves REST endpoints. Neo4j and API run via Docker Compose. Everything is testable with pytest.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, Typer, pytest, Neo4j, neo4j-python-driver, FAISS, sentence-transformers, Docker Compose

---

## File Structure

```
neo4j-graphrag-agent/
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── README.md
├── data/
│   ├── raw_docs/
│   │   ├── procurement.md
│   │   ├── inventory.md
│   │   ├── attachment_management.md
│   │   ├── approval_workflow.md
│   │   └── api_reference.md
│   ├── sample_entities.json
│   └── sample_relations.json
├── examples/
│   ├── build_graph.py
│   ├── vector_search_demo.py
│   ├── text2cypher_demo.py
│   └── graphrag_demo.py
├── src/graphrag_agent/
│   ├── __init__.py
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   └── document.py
│   ├── ontology/
│   │   ├── __init__.py
│   │   └── schema.py
│   ├── extraction/
│   │   ├── __init__.py
│   │   ├── rule_extractor.py
│   │   └── models.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── neo4j_client.py
│   │   ├── graph_loader.py
│   │   └── safety.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── embedder.py
│   │   └── vector_store.py
│   ├── text2cypher/
│   │   ├── __init__.py
│   │   ├── intent_classifier.py
│   │   ├── templates.py
│   │   └── generator.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── tools.py
│   │   └── answerer.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py
│   └── cli.py
└── tests/
    ├── __init__.py
    ├── fixtures/
    │   ├── sample_procurement.md
    │   └── sample_inventory.md
    ├── test_ingestion.py
    ├── test_ontology.py
    ├── test_extraction.py
    ├── test_graph.py
    ├── test_retrieval.py
    ├── test_text2cypher.py
    ├── test_agent.py
    └── test_api.py
```

---

## Task 1: Project Skeleton & Dependencies

**Files:**
- Create: `pyproject.toml`
- Create: `src/graphrag_agent/__init__.py`
- Create: `src/graphrag_agent/ingestion/__init__.py`
- Create: `src/graphrag_agent/ontology/__init__.py`
- Create: `src/graphrag_agent/extraction/__init__.py`
- Create: `src/graphrag_agent/graph/__init__.py`
- Create: `src/graphrag_agent/retrieval/__init__.py`
- Create: `src/graphrag_agent/text2cypher/__init__.py`
- Create: `src/graphrag_agent/agent/__init__.py`
- Create: `src/graphrag_agent/api/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/sample_procurement.md`
- Create: `.env.example`
- Create: `docker-compose.yml`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "neo4j-graphrag-agent"
version = "0.1.0"
description = "A GraphRAG agent that converts enterprise documents into a Neo4j knowledge graph."
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110.0",
    "uvicorn>=0.29.0",
    "pydantic>=2.6.0",
    "typer>=0.12.0",
    "neo4j>=5.18.0",
    "faiss-cpu>=1.8.0",
    "sentence-transformers>=2.6.0",
    "numpy>=1.26.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
]

[build-system]
requires = ["setuptools>=69.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[project.scripts]
graphrag = "graphrag_agent.cli:main"
```

- [ ] **Step 2: Create directory structure with `__init__.py` files**

Create all empty `__init__.py` files listed above. Content can be empty or minimal comments.

- [ ] **Step 3: Create sample fixture document**

`tests/fixtures/sample_procurement.md`:
```markdown
# Procurement Module

The procurement module handles purchase orders and supplier management.

## APIs

- `createPurchaseOrder` - Creates a new purchase order.
- `querySupplier` - Queries supplier information.

## Roles

- Procurement Clerk - Requires PURCHASE_CREATE permission.
- Procurement Manager - Requires PURCHASE_APPROVE permission.

## Workflow

1. Submit Request
2. Manager Approval
3. Create Order
4. Inventory Receiving
```

- [ ] **Step 4: Create `.env.example`**

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=graphragdemo
API_HOST=0.0.0.0
API_PORT=8000
```

- [ ] **Step 5: Create `docker-compose.yml`**

```yaml
version: "3.8"
services:
  neo4j:
    image: neo4j:5.18-community
    container_name: neo4j-graphrag
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/graphragdemo
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
  api:
    build: .
    container_name: graphrag-api
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=graphragdemo
    depends_on:
      - neo4j
    volumes:
      - ./data:/app/data

volumes:
  neo4j_data:
  neo4j_logs:
```

- [ ] **Step 6: Create `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY src/ ./src/
COPY data/ ./data/
COPY tests/ ./tests/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["uvicorn", "graphrag_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 7: Install dependencies and run initial test**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pip install -e ".[dev]"
pytest tests/ -v
```

Expected: PASS (empty test suite or no tests found)

- [ ] **Step 8: Commit**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
git init
git add .
git commit -m "feat: project skeleton, docker-compose, and dependencies"
```

---

## Task 2: Ingestion Module (Document Loading)

**Files:**
- Create: `src/graphrag_agent/ingestion/document.py`
- Create: `src/graphrag_agent/ingestion/loader.py`
- Test: `tests/test_ingestion.py`

- [ ] **Step 1: Write `document.py` with Pydantic model**

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Document(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="File path or source identifier")
    text: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    class Config:
        frozen = False
```

- [ ] **Step 2: Write `loader.py`**

```python
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
```

- [ ] **Step 3: Write test for ingestion**

`tests/test_ingestion.py`:
```python
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
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_ingestion.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graphrag_agent/ingestion/ tests/test_ingestion.py
git commit -m "feat: ingestion module with document loader and tests"
```

---

## Task 3: Ontology Module (Schema Definition)

**Files:**
- Create: `src/graphrag_agent/ontology/schema.py`
- Test: `tests/test_ontology.py`

- [ ] **Step 1: Write `schema.py`**

```python
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class EntityType(str, Enum):
    MODULE = "Module"
    BUSINESS_OBJECT = "BusinessObject"
    API = "API"
    ROLE = "Role"
    PERMISSION = "Permission"
    WORKFLOW = "Workflow"
    STEP = "Step"
    ERROR_CODE = "ErrorCode"
    DOCUMENT = "Document"
    CHUNK = "Chunk"


class RelationType(str, Enum):
    BELONGS_TO = "BELONGS_TO"
    USES_API = "USES_API"
    REQUIRES_PERMISSION = "REQUIRES_PERMISSION"
    HAS_STEP = "HAS_STEP"
    NEXT_STEP = "NEXT_STEP"
    RELATED_TO = "RELATED_TO"
    DEFINED_IN = "DEFINED_IN"
    CAUSES = "CAUSES"
    SOLVED_BY = "SOLVED_BY"


class Entity(BaseModel):
    id: str = Field(..., description="Unique entity identifier")
    type: EntityType = Field(..., description="Entity type")
    name: str = Field(..., description="Human-readable name")
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_doc_id: Optional[str] = Field(None, description="Source document id")

    class Config:
        frozen = False


class Relation(BaseModel):
    id: str = Field(..., description="Unique relation identifier")
    type: RelationType = Field(..., description="Relation type")
    source_id: str = Field(..., description="Source entity id")
    target_id: str = Field(..., description="Target entity id")
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = False


class OntologySchema(BaseModel):
    entity_types: List[EntityType] = Field(default_factory=lambda: list(EntityType))
    relation_types: List[RelationType] = Field(default_factory=lambda: list(RelationType))

    def validate_entity(self, entity: Entity) -> bool:
        return entity.type in self.entity_types

    def validate_relation(self, relation: Relation) -> bool:
        return relation.type in self.relation_types
```

- [ ] **Step 2: Write test for ontology**

`tests/test_ontology.py`:
```python
from graphrag_agent.ontology.schema import (
    EntityType, RelationType, Entity, Relation, OntologySchema
)


def test_entity_type_enum():
    assert EntityType.MODULE.value == "Module"
    assert EntityType.API.value == "API"
    assert len(EntityType) == 10


def test_relation_type_enum():
    assert RelationType.BELONGS_TO.value == "BELONGS_TO"
    assert RelationType.SOLVED_BY.value == "SOLVED_BY"
    assert len(RelationType) == 9


def test_entity_model():
    entity = Entity(
        id="mod_001",
        type=EntityType.MODULE,
        name="Procurement",
        properties={"description": "Procurement module"},
    )
    assert entity.type == EntityType.MODULE
    assert entity.name == "Procurement"


def test_relation_model():
    relation = Relation(
        id="rel_001",
        type=RelationType.BELONGS_TO,
        source_id="api_001",
        target_id="mod_001",
    )
    assert relation.type == RelationType.BELONGS_TO
    assert relation.source_id == "api_001"


def test_ontology_schema_validation():
    schema = OntologySchema()
    entity = Entity(id="e1", type=EntityType.API, name="createPO")
    assert schema.validate_entity(entity) is True
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_ontology.py -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add src/graphrag_agent/ontology/ tests/test_ontology.py
git commit -m "feat: ontology schema with entity and relation types"
```

---

## Task 4: Extraction Module (Rule-Based Entity/Relation Extraction)

**Files:**
- Create: `src/graphrag_agent/extraction/models.py`
- Create: `src/graphrag_agent/extraction/rule_extractor.py`
- Test: `tests/test_extraction.py`

- [ ] **Step 1: Write `models.py`**

```python
from pydantic import BaseModel, Field
from typing import List
from graphrag_agent.ontology.schema import Entity, Relation


class ExtractionResult(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
```

- [ ] **Step 2: Write `rule_extractor.py`**

```python
import re
from typing import List
from graphrag_agent.ingestion.document import Document
from graphrag_agent.ontology.schema import Entity, Relation, EntityType, RelationType
from .models import ExtractionResult


class RuleExtractor:
    def extract(self, document: Document) -> ExtractionResult:
        entities = []
        relations = []
        text = document.text

        # Extract Module from H1
        module_match = re.search(r"^#\s+(.+)\s+Module", text, re.MULTILINE | re.IGNORECASE)
        if module_match:
            mod_name = module_match.group(1).strip()
            mod_id = f"mod_{self._slug(mod_name)}"
            module = Entity(
                id=mod_id,
                type=EntityType.MODULE,
                name=mod_name,
                properties={"description": f"{mod_name} module"},
                source_doc_id=document.doc_id,
            )
            entities.append(module)

        # Extract APIs from ## APIs section
        api_section = re.search(r"##\s+APIs?\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if api_section:
            api_text = api_section.group(1)
            for line in api_text.splitlines():
                m = re.match(r"-\s+`?([^`]+)`?\s*-\s*(.+)", line)
                if m:
                    api_name = m.group(1).strip()
                    api_desc = m.group(2).strip()
                    api_id = f"api_{self._slug(api_name)}"
                    api_entity = Entity(
                        id=api_id,
                        type=EntityType.API,
                        name=api_name,
                        properties={"description": api_desc},
                        source_doc_id=document.doc_id,
                    )
                    entities.append(api_entity)
                    if module_match:
                        relations.append(Relation(
                            id=f"rel_{api_id}_belongs",
                            type=RelationType.BELONGS_TO,
                            source_id=api_id,
                            target_id=mod_id,
                        ))

        # Extract Roles from ## Roles section
        roles_section = re.search(r"##\s+Roles?\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if roles_section:
            roles_text = roles_section.group(1)
            for line in roles_text.splitlines():
                m = re.match(r"-\s+(.+?)\s*-\s*Requires?\s+(.+)\s+permission", line, re.IGNORECASE)
                if m:
                    role_name = m.group(1).strip()
                    perm_name = m.group(2).strip().upper()
                    role_id = f"role_{self._slug(role_name)}"
                    perm_id = f"perm_{self._slug(perm_name)}"
                    role_entity = Entity(
                        id=role_id,
                        type=EntityType.ROLE,
                        name=role_name,
                        source_doc_id=document.doc_id,
                    )
                    perm_entity = Entity(
                        id=perm_id,
                        type=EntityType.PERMISSION,
                        name=perm_name,
                        source_doc_id=document.doc_id,
                    )
                    entities.append(role_entity)
                    entities.append(perm_entity)
                    relations.append(Relation(
                        id=f"rel_{role_id}_req",
                        type=RelationType.REQUIRES_PERMISSION,
                        source_id=role_id,
                        target_id=perm_id,
                    ))

        # Extract Workflow Steps from numbered lists in ## Workflow section
        workflow_section = re.search(r"##\s+Workflow\s+(.+?)(?=##|$)", text, re.DOTALL | re.IGNORECASE)
        if workflow_section:
            wf_text = workflow_section.group(1)
            wf_name = f"{mod_name} Workflow" if module_match else "Unknown Workflow"
            wf_id = f"wf_{self._slug(wf_name)}"
            wf_entity = Entity(
                id=wf_id,
                type=EntityType.WORKFLOW,
                name=wf_name,
                source_doc_id=document.doc_id,
            )
            entities.append(wf_entity)
            if module_match:
                relations.append(Relation(
                    id=f"rel_{wf_id}_belongs",
                    type=RelationType.BELONGS_TO,
                    source_id=wf_id,
                    target_id=mod_id,
                ))

            steps = []
            for line in wf_text.splitlines():
                m = re.match(r"\d+\.\s+(.+)", line)
                if m:
                    step_name = m.group(1).strip()
                    step_id = f"step_{self._slug(step_name)}_{len(steps)}"
                    step_entity = Entity(
                        id=step_id,
                        type=EntityType.STEP,
                        name=step_name,
                        properties={"order": len(steps) + 1},
                        source_doc_id=document.doc_id,
                    )
                    entities.append(step_entity)
                    steps.append(step_entity)
                    relations.append(Relation(
                        id=f"rel_{wf_id}_has_{step_id}",
                        type=RelationType.HAS_STEP,
                        source_id=wf_id,
                        target_id=step_id,
                    ))

            for i in range(len(steps) - 1):
                relations.append(Relation(
                    id=f"rel_{steps[i].id}_next",
                    type=RelationType.NEXT_STEP,
                    source_id=steps[i].id,
                    target_id=steps[i + 1].id,
                ))

        return ExtractionResult(entities=entities, relations=relations)

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]+", "_", text).lower().strip("_")
```

- [ ] **Step 3: Write test for extraction**

`tests/test_extraction.py`:
```python
from graphrag_agent.ingestion.document import Document
from graphrag_agent.extraction.rule_extractor import RuleExtractor
from graphrag_agent.ontology.schema import EntityType, RelationType


def test_extract_from_sample_document():
    doc = Document(
        doc_id="procurement",
        title="Procurement Module",
        source="tests/fixtures/sample_procurement.md",
        text="""# Procurement Module

The procurement module handles purchase orders and supplier management.

## APIs

- `createPurchaseOrder` - Creates a new purchase order.
- `querySupplier` - Queries supplier information.

## Roles

- Procurement Clerk - Requires PURCHASE_CREATE permission.
- Procurement Manager - Requires PURCHASE_APPROVE permission.

## Workflow

1. Submit Request
2. Manager Approval
3. Create Order
4. Inventory Receiving
""",
    )
    extractor = RuleExtractor()
    result = extractor.extract(doc)

    entity_types = {e.type for e in result.entities}
    assert EntityType.MODULE in entity_types
    assert EntityType.API in entity_types
    assert EntityType.ROLE in entity_types
    assert EntityType.PERMISSION in entity_types
    assert EntityType.WORKFLOW in entity_types
    assert EntityType.STEP in entity_types

    # Check relations
    relation_types = {r.type for r in result.relations}
    assert RelationType.BELONGS_TO in relation_types
    assert RelationType.REQUIRES_PERMISSION in relation_types
    assert RelationType.HAS_STEP in relation_types
    assert RelationType.NEXT_STEP in relation_types

    # Check module name
    module = next(e for e in result.entities if e.type == EntityType.MODULE)
    assert module.name == "Procurement"

    # Check API count
    apis = [e for e in result.entities if e.type == EntityType.API]
    assert len(apis) == 2

    # Check step count
    steps = [e for e in result.entities if e.type == EntityType.STEP]
    assert len(steps) == 4

    # Check next_step relations
    next_steps = [r for r in result.relations if r.type == RelationType.NEXT_STEP]
    assert len(next_steps) == 3
```

- [ ] **Step 4: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_extraction.py -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/graphrag_agent/extraction/ tests/test_extraction.py
git commit -m "feat: rule-based entity and relation extraction with tests"
```

---

## Task 5: Graph Module (Neo4j Client + Safety + Loader)

**Files:**
- Create: `src/graphrag_agent/graph/safety.py`
- Create: `src/graphrag_agent/graph/neo4j_client.py`
- Create: `src/graphrag_agent/graph/graph_loader.py`
- Test: `tests/test_graph.py`

- [ ] **Step 1: Write `safety.py`**

```python
import re
from typing import List

ALLOWED_KEYWORDS = {
    "MATCH", "RETURN", "WHERE", "LIMIT", "ORDER", "BY", "AS",
    "WITH", "UNWIND", "COLLECT", "COUNT", "DISTINCT", "OPTIONAL",
    "AND", "OR", "NOT", "IN", "IS", "NULL", "TRUE", "FALSE",
    "STARTS", "ENDS", "CONTAINS", "CASE", "WHEN", "THEN", "ELSE",
}

FORBIDDEN_KEYWORDS = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "CSV", "apoc", "gds", "dbms",
    "GRANT", "REVOKE", "DENY", "ROLE", "USER", "PASSWORD",
}


class CypherSafetyError(Exception):
    pass


def validate_read_only(cypher: str) -> bool:
    upper = cypher.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper:
            raise CypherSafetyError(f"Forbidden keyword detected: {keyword}")
    return True


def sanitize_cypher(cypher: str) -> str:
    cleaned = cypher.strip()
    if not cleaned:
        raise CypherSafetyError("Empty Cypher query")
    validate_read_only(cleaned)
    return cleaned
```

- [ ] **Step 2: Write `neo4j_client.py`**

```python
import os
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from .safety import sanitize_cypher, CypherSafetyError


class Neo4jClient:
    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "neo4j")
        self._driver = None

    def connect(self):
        self._driver = GraphDatabase.driver(
            self.uri, auth=(self.user, self.password)
        )
        return self

    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

    def run_safe(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        parameters = parameters or {}
        sanitize_cypher(cypher)
        with self._driver.session() as session:
            result = session.run(cypher, parameters)
            return [record.data() for record in result]

    def init_constraints(self):
        constraints = [
            "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE",
        ]
        with self._driver.session() as session:
            for cypher in constraints:
                try:
                    session.run(cypher)
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        raise

    def is_connected(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

- [ ] **Step 3: Write `graph_loader.py`**

```python
from typing import List
from graphrag_agent.ontology.schema import Entity, Relation
from .neo4j_client import Neo4jClient


class GraphLoader:
    def __init__(self, client: Neo4jClient):
        self.client = client

    def load_entities(self, entities: List[Entity]):
        for entity in entities:
            cypher = """
            MERGE (e:Entity {id: $id})
            SET e.type = $type,
                e.name = $name,
                e.properties = $properties,
                e.source_doc_id = $source_doc_id
            """
            self.client._driver.session().run(
                cypher,
                {
                    "id": entity.id,
                    "type": entity.type.value,
                    "name": entity.name,
                    "properties": entity.properties,
                    "source_doc_id": entity.source_doc_id or "",
                }
            )

    def load_relations(self, relations: List[Relation]):
        for relation in relations:
            cypher = """
            MATCH (a:Entity {id: $source_id}), (b:Entity {id: $target_id})
            MERGE (a)-[r:RELATION {id: $id, type: $type}]->(b)
            SET r.properties = $properties
            """
            self.client._driver.session().run(
                cypher,
                {
                    "id": relation.id,
                    "type": relation.type.value,
                    "source_id": relation.source_id,
                    "target_id": relation.target_id,
                    "properties": relation.properties,
                }
            )

    def load_all(self, entities: List[Entity], relations: List[Relation]):
        self.load_entities(entities)
        self.load_relations(relations)

    def clear_all(self):
        self.client._driver.session().run("MATCH (n) DETACH DELETE n")
```

- [ ] **Step 4: Write test for graph module**

`tests/test_graph.py`:
```python
import pytest
from graphrag_agent.graph.safety import validate_read_only, CypherSafetyError, sanitize_cypher
from graphrag_agent.graph.neo4j_client import Neo4jClient


def test_safety_allows_match():
    assert validate_read_only("MATCH (n) RETURN n") is True


def test_safety_rejects_create():
    with pytest.raises(CypherSafetyError):
        validate_read_only("CREATE (n:Node)")


def test_safety_rejects_delete():
    with pytest.raises(CypherSafetyError):
        validate_read_only("MATCH (n) DELETE n")


def test_sanitize_empty():
    with pytest.raises(CypherSafetyError):
        sanitize_cypher("   ")


def test_client_env_defaults():
    client = Neo4jClient()
    assert client.uri == "bolt://localhost:7687"
    assert client.user == "neo4j"
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_graph.py -v
```

Expected: PASS (unit tests for safety and client creation; integration tests require Neo4j)

- [ ] **Step 6: Commit**

```bash
git add src/graphrag_agent/graph/ tests/test_graph.py
git commit -m "feat: Neo4j client with safety validation and graph loader"
```

---

## Task 6: Retrieval Module (Chunking + Embedding + FAISS)

**Files:**
- Create: `src/graphrag_agent/retrieval/chunker.py`
- Create: `src/graphrag_agent/retrieval/embedder.py`
- Create: `src/graphrag_agent/retrieval/vector_store.py`
- Test: `tests/test_retrieval.py`

- [ ] **Step 1: Write `chunker.py`**

```python
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
```

- [ ] **Step 2: Write `embedder.py`**

```python
from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, texts: List[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def encode_query(self, text: str) -> np.ndarray:
        return self.model.encode(text, convert_to_numpy=True)
```

- [ ] **Step 3: Write `vector_store.py`**

```python
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
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine with normalized vectors
        self.documents: Dict[str, Document] = {}
        self.vectors: Dict[int, str] = {}

    def add_documents(self, documents: List[Document]):
        if not documents:
            return
        texts = [doc.text for doc in documents]
        vectors = self.embedder.encode(texts)
        # Normalize for cosine similarity via inner product
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
```

- [ ] **Step 4: Write test for retrieval**

`tests/test_retrieval.py`:
```python
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
    assert isinstance(vecs, type(vecs))


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
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_retrieval.py -v
```

Expected: PASS (first run may download sentence-transformers model, takes ~30s)

- [ ] **Step 6: Commit**

```bash
git add src/graphrag_agent/retrieval/ tests/test_retrieval.py
git commit -m "feat: retrieval module with chunking, embedding, and FAISS vector store"
```

---

## Task 7: Text2Cypher Module (Intent Classification + Templates)

**Files:**
- Create: `src/graphrag_agent/text2cypher/intent_classifier.py`
- Create: `src/graphrag_agent/text2cypher/templates.py`
- Create: `src/graphrag_agent/text2cypher/generator.py`
- Test: `tests/test_text2cypher.py`

- [ ] **Step 1: Write `intent_classifier.py`**

```python
from enum import Enum
from typing import Optional
import re


class QuestionIntent(str, Enum):
    API_BY_MODULE = "api_by_module"
    ROLES_BY_PERMISSION = "roles_by_permission"
    WORKFLOW_STEPS = "workflow_steps"
    ERROR_SOLUTION = "error_solution"
    BUSINESS_OBJECT_RELATION = "business_object_relation"
    UNKNOWN = "unknown"


class IntentClassifier:
    def classify(self, question: str) -> QuestionIntent:
        q = question.lower()

        if any(k in q for k in ["api", "interface", "method"]) and any(k in q for k in ["module", "mod"]):
            return QuestionIntent.API_BY_MODULE

        if any(k in q for k in ["role", "who can", "approve", "permission"]):
            return QuestionIntent.ROLES_BY_PERMISSION

        if any(k in q for k in ["step", "flow", "process", "workflow", "from", "to"]):
            return QuestionIntent.WORKFLOW_STEPS

        if any(k in q for k in ["error", "fail", "fix", "solve", "issue"]):
            return QuestionIntent.ERROR_SOLUTION

        if any(k in q for k in ["related", "relation", "connect", "link"]):
            return QuestionIntent.BUSINESS_OBJECT_RELATION

        return QuestionIntent.UNKNOWN
```

- [ ] **Step 2: Write `templates.py`**

```python
from typing import Dict
from .intent_classifier import QuestionIntent


CYPHERS: Dict[QuestionIntent, str] = {
    QuestionIntent.API_BY_MODULE: """
MATCH (m:Entity {type: 'Module', name: $module_name})<-[:RELATION {type: 'BELONGS_TO'}]-(api:Entity {type: 'API'})
RETURN api.name AS api_name, api.properties.description AS description
""",
    QuestionIntent.ROLES_BY_PERMISSION: """
MATCH (perm:Entity {type: 'Permission', name: $permission_name})
<-[:RELATION {type: 'REQUIRES_PERMISSION'}]-(role:Entity {type: 'Role'})
RETURN role.name AS role_name
""",
    QuestionIntent.WORKFLOW_STEPS: """
MATCH (wf:Entity {type: 'Workflow', name: $workflow_name})-[:RELATION {type: 'HAS_STEP'}]->(s:Entity {type: 'Step'})
OPTIONAL MATCH (s)-[:RELATION {type: 'NEXT_STEP'}]->(next:Entity {type: 'Step'})
RETURN s.name AS step_name, s.properties.order AS step_order, next.name AS next_step
ORDER BY s.properties.order
""",
    QuestionIntent.ERROR_SOLUTION: """
MATCH (err:Entity {type: 'ErrorCode', name: $error_name})
OPTIONAL MATCH (err)-[:RELATION {type: 'CAUSES'}]->(cause:Entity)
OPTIONAL MATCH (err)-[:RELATION {type: 'SOLVED_BY'}]->(solution:Entity)
RETURN err.name AS error, cause.name AS cause, solution.name AS solution
""",
    QuestionIntent.BUSINESS_OBJECT_RELATION: """
MATCH (bo:Entity {type: 'BusinessObject', name: $object_name})-[:RELATION]-(related:Entity)
RETURN related.name AS related_name, related.type AS related_type
""",
}


def get_template(intent: QuestionIntent) -> str:
    return CYPHERS.get(intent, "")
```

- [ ] **Step 3: Write `generator.py`**

```python
from typing import Optional, Dict, Any
from .intent_classifier import IntentClassifier, QuestionIntent
from .templates import get_template


class CypherGenerator:
    def __init__(self):
        self.classifier = IntentClassifier()

    def generate(self, question: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        parameters = parameters or {}
        intent = self.classifier.classify(question)
        template = get_template(intent)

        if not template or intent == QuestionIntent.UNKNOWN:
            return {
                "cypher": "",
                "intent": intent.value,
                "confidence": 0.0,
                "parameters": parameters,
            }

        # Simple parameter substitution (production should use neo4j driver parameters)
        cypher = template
        for key, value in parameters.items():
            placeholder = f"${key}"
            if isinstance(value, str):
                cypher = cypher.replace(placeholder, f"'{value}'")
            else:
                cypher = cypher.replace(placeholder, str(value))

        return {
            "cypher": cypher.strip(),
            "intent": intent.value,
            "confidence": 0.85,
            "parameters": parameters,
        }
```

- [ ] **Step 4: Write test for text2cypher**

`tests/test_text2cypher.py`:
```python
from graphrag_agent.text2cypher.intent_classifier import IntentClassifier, QuestionIntent
from graphrag_agent.text2cypher.generator import CypherGenerator


def test_classify_api_by_module():
    clf = IntentClassifier()
    assert clf.classify("Which APIs are in the procurement module?") == QuestionIntent.API_BY_MODULE


def test_classify_workflow_steps():
    clf = IntentClassifier()
    assert clf.classify("What are the steps in the purchase workflow?") == QuestionIntent.WORKFLOW_STEPS


def test_classify_roles_by_permission():
    clf = IntentClassifier()
    assert clf.classify("Which roles can approve purchase orders?") == QuestionIntent.ROLES_BY_PERMISSION


def test_generator_produces_cypher():
    gen = CypherGenerator()
    result = gen.generate(
        "Which APIs are in the procurement module?",
        {"module_name": "Procurement"},
    )
    assert result["intent"] == "api_by_module"
    assert result["confidence"] == 0.85
    assert "MATCH" in result["cypher"]
    assert "'Procurement'" in result["cypher"]


def test_generator_unknown_fallback():
    gen = CypherGenerator()
    result = gen.generate("What is the weather today?")
    assert result["cypher"] == ""
    assert result["confidence"] == 0.0
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_text2cypher.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/graphrag_agent/text2cypher/ tests/test_text2cypher.py
git commit -m "feat: template-based text2cypher with intent classification"
```

---

## Task 8: Agent Module (Router + Tools + Answerer)

**Files:**
- Create: `src/graphrag_agent/agent/tools.py`
- Create: `src/graphrag_agent/agent/router.py`
- Create: `src/graphrag_agent/agent/answerer.py`
- Test: `tests/test_agent.py`

- [ ] **Step 1: Write `tools.py`**

```python
from typing import List, Dict, Any, Optional
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.retrieval.vector_store import VectorStore, SearchResult
from graphrag_agent.text2cypher.generator import CypherGenerator
from graphrag_agent.text2cypher.intent_classifier import QuestionIntent


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None


class ToolRegistry:
    def __init__(self, neo4j: Neo4jClient, vector_store: VectorStore):
        self.neo4j = neo4j
        self.vector_store = vector_store
        self.cypher_generator = CypherGenerator()

    def search_vector_db(self, query: str, top_k: int = 5) -> ToolResult:
        try:
            results = self.vector_store.search(query, top_k=top_k)
            return ToolResult(
                tool_name="search_vector_db",
                success=True,
                data=[r.model_dump() for r in results],
            )
        except Exception as e:
            return ToolResult(
                tool_name="search_vector_db",
                success=False,
                data=[],
                error=str(e),
            )

    def generate_cypher(self, question: str, parameters: Optional[Dict[str, Any]] = None) -> ToolResult:
        try:
            result = self.cypher_generator.generate(question, parameters)
            return ToolResult(
                tool_name="generate_cypher",
                success=result["cypher"] != "",
                data=result,
            )
        except Exception as e:
            return ToolResult(
                tool_name="generate_cypher",
                success=False,
                data={},
                error=str(e),
            )

    def query_neo4j(self, cypher: str) -> ToolResult:
        try:
            records = self.neo4j.run_safe(cypher)
            return ToolResult(
                tool_name="query_neo4j",
                success=True,
                data=records,
            )
        except Exception as e:
            return ToolResult(
                tool_name="query_neo4j",
                success=False,
                data=[],
                error=str(e),
            )
```

Wait, I need to add pydantic import. Let me rewrite with proper imports.

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.retrieval.vector_store import VectorStore
from graphrag_agent.text2cypher.generator import CypherGenerator


class ToolResult(BaseModel):
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None


class ToolRegistry:
    def __init__(self, neo4j: Neo4jClient, vector_store: VectorStore):
        self.neo4j = neo4j
        self.vector_store = vector_store
        self.cypher_generator = CypherGenerator()

    def search_vector_db(self, query: str, top_k: int = 5) -> ToolResult:
        try:
            results = self.vector_store.search(query, top_k=top_k)
            return ToolResult(
                tool_name="search_vector_db",
                success=True,
                data=[r.model_dump() for r in results],
            )
        except Exception as e:
            return ToolResult(
                tool_name="search_vector_db",
                success=False,
                data=[],
                error=str(e),
            )

    def generate_cypher(self, question: str, parameters: Optional[Dict[str, Any]] = None) -> ToolResult:
        try:
            result = self.cypher_generator.generate(question, parameters)
            return ToolResult(
                tool_name="generate_cypher",
                success=result["cypher"] != "",
                data=result,
            )
        except Exception as e:
            return ToolResult(
                tool_name="generate_cypher",
                success=False,
                data={},
                error=str(e),
            )

    def query_neo4j(self, cypher: str) -> ToolResult:
        try:
            records = self.neo4j.run_safe(cypher)
            return ToolResult(
                tool_name="query_neo4j",
                success=True,
                data=records,
            )
        except Exception as e:
            return ToolResult(
                tool_name="query_neo4j",
                success=False,
                data=[],
                error=str(e),
            )
```

- [ ] **Step 2: Write `router.py`**

```python
from typing import List, Optional
from graphrag_agent.text2cypher.intent_classifier import IntentClassifier, QuestionIntent


class Router:
    def __init__(self):
        self.classifier = IntentClassifier()

    def decide_mode(self, question: str) -> str:
        intent = self.classifier.classify(question)

        if intent in {
            QuestionIntent.API_BY_MODULE,
            QuestionIntent.WORKFLOW_STEPS,
            QuestionIntent.ROLES_BY_PERMISSION,
            QuestionIntent.BUSINESS_OBJECT_RELATION,
        }:
            return "graph"

        if intent == QuestionIntent.ERROR_SOLUTION:
            return "hybrid"

        return "vector"

    def select_tools(self, mode: str) -> List[str]:
        if mode == "graph":
            return ["generate_cypher", "query_neo4j"]
        if mode == "vector":
            return ["search_vector_db"]
        if mode == "hybrid":
            return ["generate_cypher", "query_neo4j", "search_vector_db"]
        return ["search_vector_db"]
```

- [ ] **Step 3: Write `answerer.py`**

```python
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class AnswerOutput(BaseModel):
    answer: str
    graph_evidence: List[Dict[str, Any]]
    text_evidence: List[Dict[str, Any]]
    cypher: Optional[str] = None
    tools_used: List[str]
    mode: str


class Answerer:
    def generate_answer(
        self,
        question: str,
        mode: str,
        graph_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        cypher: Optional[str] = None,
        tools_used: List[str] = None,
    ) -> AnswerOutput:
        tools_used = tools_used or []
        graph_evidence = graph_results
        text_evidence = vector_results

        # Build answer from evidence (no LLM, template-based)
        answer_parts = []

        if graph_evidence:
            answer_parts.append("Based on the knowledge graph:")
            for i, record in enumerate(graph_evidence[:5], 1):
                items = ", ".join(f"{k}={v}" for k, v in record.items() if v is not None)
                answer_parts.append(f"{i}. {items}")

        if text_evidence:
            answer_parts.append("\nFrom the documentation:")
            for i, record in enumerate(text_evidence[:3], 1):
                text = record.get("text", "")
                source = record.get("source", "unknown")
                answer_parts.append(f"{i}. [{source}] {text[:200]}")

        if not answer_parts:
            answer = "I could not find relevant information."
        else:
            answer = "\n".join(answer_parts)

        return AnswerOutput(
            answer=answer,
            graph_evidence=graph_evidence,
            text_evidence=text_evidence,
            cypher=cypher,
            tools_used=tools_used,
            mode=mode,
        )
```

- [ ] **Step 4: Write test for agent**

`tests/test_agent.py`:
```python
from graphrag_agent.agent.router import Router
from graphrag_agent.agent.answerer import Answerer, AnswerOutput
from graphrag_agent.agent.tools import ToolRegistry
from graphrag_agent.text2cypher.intent_classifier import QuestionIntent


def test_router_graph_mode_for_api_question():
    router = Router()
    mode = router.decide_mode("Which APIs are in the procurement module?")
    assert mode == "graph"
    tools = router.select_tools(mode)
    assert "generate_cypher" in tools
    assert "query_neo4j" in tools


def test_router_hybrid_mode_for_error_question():
    router = Router()
    mode = router.decide_mode("Why does attachment upload fail?")
    assert mode == "hybrid"


def test_router_vector_mode_for_general_question():
    router = Router()
    mode = router.decide_mode("How does the system work?")
    assert mode == "vector"


def test_answerer_with_graph_evidence():
    answerer = Answerer()
    graph_results = [{"api_name": "createPurchaseOrder", "description": "Creates PO"}]
    output = answerer.generate_answer(
        question="Which APIs?",
        mode="graph",
        graph_results=graph_results,
        vector_results=[],
        cypher="MATCH ...",
        tools_used=["generate_cypher", "query_neo4j"],
    )
    assert isinstance(output, AnswerOutput)
    assert "createPurchaseOrder" in output.answer
    assert output.cypher == "MATCH ..."
    assert output.mode == "graph"


def test_answerer_empty_evidence():
    answerer = Answerer()
    output = answerer.generate_answer(
        question="What is X?",
        mode="vector",
        graph_results=[],
        vector_results=[],
    )
    assert "could not find" in output.answer
```

- [ ] **Step 5: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_agent.py -v
```

Expected: PASS (some tests may need mocked Neo4j/VectorStore, but ToolRegistry tests should pass with mock objects if they don't instantiate connections)

Wait, actually the tests for `ToolRegistry` may need actual instances. Let me make sure the tests only test Router and Answerer which don't require external connections. The tests above should be fine.

- [ ] **Step 6: Commit**

```bash
git add src/graphrag_agent/agent/ tests/test_agent.py
git commit -m "feat: agent module with router, tools, and answerer"
```

---

## Task 9: FastAPI Application + CLI

**Files:**
- Create: `src/graphrag_agent/api/main.py`
- Create: `src/graphrag_agent/cli.py`
- Test: `tests/test_api.py`

- [ ] **Step 1: Write `api/main.py`**

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os

from graphrag_agent.ingestion.loader import DocumentLoader
from graphrag_agent.extraction.rule_extractor import RuleExtractor
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.graph.graph_loader import GraphLoader
from graphrag_agent.retrieval.embedder import Embedder
from graphrag_agent.retrieval.chunker import Chunker
from graphrag_agent.retrieval.vector_store import VectorStore
from graphrag_agent.text2cypher.generator import CypherGenerator
from graphrag_agent.agent.router import Router
from graphrag_agent.agent.tools import ToolRegistry
from graphrag_agent.agent.answerer import Answerer

app = FastAPI(title="Neo4j GraphRAG Agent", version="0.1.0")

# Shared state (simplified for MVP)
neo4j_client: Neo4jClient = None
vector_store: VectorStore = None
tool_registry: ToolRegistry = None
router: Router = Router()
answerer: Answerer = Answerer()


@app.on_event("startup")
async def startup():
    global neo4j_client, vector_store, tool_registry
    neo4j_client = Neo4jClient().connect()
    neo4j_client.init_constraints()
    embedder = Embedder()
    vector_store = VectorStore(embedder)
    tool_registry = ToolRegistry(neo4j_client, vector_store)


@app.on_event("shutdown")
async def shutdown():
    if neo4j_client:
        neo4j_client.close()


@app.get("/health")
async def health():
    return {"status": "ok", "neo4j_connected": neo4j_client.is_connected() if neo4j_client else False}


class BuildGraphRequest(BaseModel):
    docs_dir: str = "data/raw_docs"


@app.post("/graph/build")
async def build_graph(request: BuildGraphRequest):
    try:
        loader = DocumentLoader(request.docs_dir)
        docs = loader.load_all()
        extractor = RuleExtractor()
        all_entities = []
        all_relations = []
        for doc in docs:
            result = extractor.extract(doc)
            all_entities.extend(result.entities)
            all_relations.extend(result.relations)

        # Deduplicate by id
        entity_map = {e.id: e for e in all_entities}
        relation_map = {r.id: r for r in all_relations}

        graph_loader = GraphLoader(neo4j_client)
        graph_loader.clear_all()
        graph_loader.load_all(list(entity_map.values()), list(relation_map.values()))

        # Build vector index
        chunker = Chunker()
        for doc in docs:
            chunks = chunker.chunk(doc)
            vector_store.add_documents(chunks)

        return {
            "entities_loaded": len(entity_map),
            "relations_loaded": len(relation_map),
            "documents_loaded": len(docs),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/search/vector")
async def search_vector(request: SearchRequest):
    result = tool_registry.search_vector_db(request.query, request.top_k)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {"results": result.data}


class CypherRequest(BaseModel):
    question: str
    parameters: Optional[Dict[str, Any]] = None


@app.post("/cypher/generate")
async def generate_cypher(request: CypherRequest):
    result = tool_registry.generate_cypher(request.question, request.parameters)
    if not result.success:
        raise HTTPException(status_code=400, detail="Could not generate cypher for this question")
    return result.data


class QueryRequest(BaseModel):
    cypher: str


@app.post("/graph/query")
async def query_graph(request: QueryRequest):
    result = tool_registry.query_neo4j(request.cypher)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return {"records": result.data}


class AskRequest(BaseModel):
    question: str
    mode: Optional[str] = "auto"


@app.post("/agent/ask")
async def ask_agent(request: AskRequest):
    try:
        mode = request.mode if request.mode != "auto" else router.decide_mode(request.question)
        tools = router.select_tools(mode)
        graph_results = []
        vector_results = []
        cypher_used = None

        if "generate_cypher" in tools:
            cypher_result = tool_registry.generate_cypher(request.question)
            if cypher_result.success:
                cypher_used = cypher_result.data["cypher"]
                query_result = tool_registry.query_neo4j(cypher_used)
                if query_result.success:
                    graph_results = query_result.data

        if "search_vector_db" in tools:
            vector_result = tool_registry.search_vector_db(request.question)
            if vector_result.success:
                vector_results = vector_result.data

        output = answerer.generate_answer(
            question=request.question,
            mode=mode,
            graph_results=graph_results,
            vector_results=vector_results,
            cypher=cypher_used,
            tools_used=tools,
        )
        return output.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Write `cli.py`**

```python
import typer
from pathlib import Path
from graphrag_agent.ingestion.loader import DocumentLoader
from graphrag_agent.extraction.rule_extractor import RuleExtractor
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.graph.graph_loader import GraphLoader
from graphrag_agent.retrieval.embedder import Embedder
from graphrag_agent.retrieval.chunker import Chunker
from graphrag_agent.retrieval.vector_store import VectorStore
from graphrag_agent.text2cypher.generator import CypherGenerator
from graphrag_agent.agent.router import Router
from graphrag_agent.agent.tools import ToolRegistry
from graphrag_agent.agent.answerer import Answerer

app = typer.Typer()


@app.command()
def build_graph(docs_dir: str = "data/raw_docs"):
    """Build the knowledge graph from documents."""
    typer.echo(f"Loading documents from {docs_dir}...")
    loader = DocumentLoader(docs_dir)
    docs = loader.load_all()
    typer.echo(f"Loaded {len(docs)} documents")

    extractor = RuleExtractor()
    all_entities = []
    all_relations = []
    for doc in docs:
        result = extractor.extract(doc)
        all_entities.extend(result.entities)
        all_relations.extend(result.relations)

    entity_map = {e.id: e for e in all_entities}
    relation_map = {r.id: r for r in all_relations}

    with Neo4jClient() as client:
        client.init_constraints()
        graph_loader = GraphLoader(client)
        graph_loader.clear_all()
        graph_loader.load_all(list(entity_map.values()), list(relation_map.values()))

    embedder = Embedder()
    store = VectorStore(embedder)
    chunker = Chunker()
    for doc in docs:
        chunks = chunker.chunk(doc)
        store.add_documents(chunks)

    typer.echo(f"Loaded {len(entity_map)} entities and {len(relation_map)} relations")
    typer.echo("Graph and vector index built successfully")


@app.command()
def ask(question: str, mode: str = "auto"):
    """Ask a question to the GraphRAG agent."""
    router = Router()
    answerer = Answerer()
    with Neo4jClient() as client:
        embedder = Embedder()
        store = VectorStore(embedder)
        tools = ToolRegistry(client, store)

        actual_mode = mode if mode != "auto" else router.decide_mode(question)
        tool_names = router.select_tools(actual_mode)

        graph_results = []
        vector_results = []
        cypher_used = None

        if "generate_cypher" in tool_names:
            cypher_result = tools.generate_cypher(question)
            if cypher_result.success:
                cypher_used = cypher_result.data["cypher"]
                query_result = tools.query_neo4j(cypher_used)
                if query_result.success:
                    graph_results = query_result.data

        if "search_vector_db" in tool_names:
            vector_result = tools.search_vector_db(question)
            if vector_result.success:
                vector_results = vector_result.data

        output = answerer.generate_answer(
            question=question,
            mode=actual_mode,
            graph_results=graph_results,
            vector_results=vector_results,
            cypher=cypher_used,
            tools_used=tool_names,
        )

    typer.echo(f"Mode: {output.mode}")
    typer.echo(f"Tools: {', '.join(output.tools_used)}")
    if output.cypher:
        typer.echo(f"Cypher: {output.cypher}")
    typer.echo("\nAnswer:")
    typer.echo(output.answer)


def main():
    app()
```

- [ ] **Step 3: Write test for API**

`tests/test_api.py`:
```python
from fastapi.testclient import TestClient
from graphrag_agent.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
```

Note: The `/graph/build` and other endpoints may fail if Neo4j is not running. We can add mock tests or skip them. The test above just tests the health endpoint.

- [ ] **Step 4: Run tests**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/test_api.py -v
```

Expected: PASS for health endpoint; other tests may be skipped if Neo4j unavailable.

- [ ] **Step 5: Commit**

```bash
git add src/graphrag_agent/api/ src/graphrag_agent/cli.py tests/test_api.py
git commit -m "feat: FastAPI app and CLI with all endpoints"
```

---

## Task 10: Sample Documents + Demo Scripts + README

**Files:**
- Create: `data/raw_docs/procurement.md`
- Create: `data/raw_docs/inventory.md`
- Create: `data/raw_docs/attachment_management.md`
- Create: `data/raw_docs/approval_workflow.md`
- Create: `data/raw_docs/api_reference.md`
- Create: `examples/build_graph.py`
- Create: `examples/text2cypher_demo.py`
- Create: `examples/graphrag_demo.py`
- Modify: `README.md`

- [ ] **Step 1: Create sample ERP documents**

`data/raw_docs/procurement.md`:
```markdown
# Procurement Module

The procurement module handles purchase orders and supplier management.

## APIs

- `createPurchaseOrder` - Creates a new purchase order.
- `querySupplier` - Queries supplier information.
- `approvePurchaseOrder` - Approves a pending purchase order.

## Roles

- Procurement Clerk - Requires PURCHASE_CREATE permission.
- Procurement Manager - Requires PURCHASE_APPROVE permission.

## Workflow

1. Submit Request
2. Manager Approval
3. Create Order
4. Inventory Receiving

## Business Objects

- PurchaseOrder
- Supplier
- PurchaseRequest
```

`data/raw_docs/inventory.md`:
```markdown
# Inventory Module

The inventory module manages stock levels and warehouse operations.

## APIs

- `queryInventory` - Queries current inventory levels.
- `updateStock` - Updates stock quantity.
- `transferStock` - Transfers stock between warehouses.

## Roles

- Warehouse Clerk - Requires INVENTORY_QUERY permission.
- Warehouse Manager - Requires INVENTORY_UPDATE permission.

## Workflow

1. Stock Inquiry
2. Check Availability
3. Update Stock
4. Confirm Receipt

## Business Objects

- InventoryItem
- Warehouse
- StockTransfer
```

`data/raw_docs/attachment_management.md`:
```markdown
# Attachment Management Module

The attachment management module handles file uploads and document attachments.

## APIs

- `uploadAttachment` - Uploads a file attachment.
- `downloadAttachment` - Downloads an attached file.
- `deleteAttachment` - Deletes an attachment.

## Error Codes

- `ATT_001` - File size exceeds limit. Solved by compressing file or using smaller file.
- `ATT_002` - Unsupported file format. Solved by converting to supported format.
- `ATT_003` - Upload timeout. Solved by checking network connection.

## Roles

- System User - Requires ATTACHMENT_UPLOAD permission.
- Administrator - Requires ATTACHMENT_DELETE permission.
```

`data/raw_docs/approval_workflow.md`:
```markdown
# Approval Workflow Module

The approval workflow module manages business process approvals.

## APIs

- `submitApproval` - Submits an item for approval.
- `approveRequest` - Approves a pending request.
- `rejectRequest` - Rejects a pending request.

## Workflow

1. Submit Request
2. Review Request
3. Manager Approval
4. Finance Review
5. Final Approval

## Roles

- Requester - Requires APPROVAL_SUBMIT permission.
- Manager - Requires APPROVAL_MANAGER permission.
- Finance Reviewer - Requires APPROVAL_FINANCE permission.
```

`data/raw_docs/api_reference.md`:
```markdown
# API Reference

## Cross-Module APIs

- `convertPurchaseToInventory` - Converts a purchase order to inventory stock. Used by Procurement and Inventory modules.
- `notifyApprovalComplete` - Sends notification when approval is complete. Used by Approval Workflow module.
- `attachDocumentToOrder` - Attaches a document to a purchase order. Used by Procurement and Attachment Management modules.

## Permissions

- PURCHASE_CREATE - Create purchase orders.
- PURCHASE_APPROVE - Approve purchase orders.
- INVENTORY_QUERY - Query inventory.
- INVENTORY_UPDATE - Update inventory.
- ATTACHMENT_UPLOAD - Upload attachments.
- ATTACHMENT_DELETE - Delete attachments.
- APPROVAL_SUBMIT - Submit approval requests.
- APPROVAL_MANAGER - Manager approval authority.
- APPROVAL_FINANCE - Finance review authority.
```

- [ ] **Step 2: Create demo scripts**

`examples/build_graph.py`:
```python
#!/usr/bin/env python3
"""Demo: Build the knowledge graph from sample documents."""
from graphrag_agent.ingestion.loader import DocumentLoader
from graphrag_agent.extraction.rule_extractor import RuleExtractor
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.graph.graph_loader import GraphLoader
from graphrag_agent.retrieval.embedder import Embedder
from graphrag_agent.retrieval.chunker import Chunker
from graphrag_agent.retrieval.vector_store import VectorStore

def main():
    print("Loading documents...")
    loader = DocumentLoader("data/raw_docs")
    docs = loader.load_all()
    print(f"Loaded {len(docs)} documents")

    print("Extracting entities and relations...")
    extractor = RuleExtractor()
    all_entities = []
    all_relations = []
    for doc in docs:
        result = extractor.extract(doc)
        all_entities.extend(result.entities)
        all_relations.extend(result.relations)
        print(f"  {doc.title}: {len(result.entities)} entities, {len(result.relations)} relations")

    entity_map = {e.id: e for e in all_entities}
    relation_map = {r.id: r for r in all_relations}

    print("Loading into Neo4j...")
    with Neo4jClient() as client:
        client.init_constraints()
        graph_loader = GraphLoader(client)
        graph_loader.clear_all()
        graph_loader.load_all(list(entity_map.values()), list(relation_map.values()))
    print(f"Loaded {len(entity_map)} entities and {len(relation_map)} relations")

    print("Building vector index...")
    embedder = Embedder()
    store = VectorStore(embedder)
    chunker = Chunker()
    for doc in docs:
        chunks = chunker.chunk(doc)
        store.add_documents(chunks)
    print("Vector index built")

if __name__ == "__main__":
    main()
```

`examples/text2cypher_demo.py`:
```python
#!/usr/bin/env python3
"""Demo: Template-based text2cypher."""
from graphrag_agent.text2cypher.generator import CypherGenerator

QUESTIONS = [
    ("Which APIs are available in the procurement module?", {"module_name": "Procurement"}),
    ("Which roles can approve purchase orders?", {"permission_name": "PURCHASE_APPROVE"}),
    ("What are the steps in the purchase workflow?", {"workflow_name": "Procurement Workflow"}),
]

def main():
    gen = CypherGenerator()
    for question, params in QUESTIONS:
        result = gen.generate(question, params)
        print(f"Q: {question}")
        print(f"Intent: {result['intent']}")
        print(f"Cypher:\n{result['cypher']}\n")

if __name__ == "__main__":
    main()
```

`examples/graphrag_demo.py`:
```python
#!/usr/bin/env python3
"""Demo: GraphRAG agent answering questions."""
from graphrag_agent.agent.router import Router
from graphrag_agent.agent.answerer import Answerer
from graphrag_agent.agent.tools import ToolRegistry
from graphrag_agent.graph.neo4j_client import Neo4jClient
from graphrag_agent.retrieval.embedder import Embedder
from graphrag_agent.retrieval.vector_store import VectorStore

QUESTIONS = [
    "Which APIs are available in the procurement module?",
    "Which roles can approve purchase orders?",
    "What are the steps in the purchase workflow?",
    "Why does attachment upload fail?",
    "Which modules are involved when a purchase order is converted into inventory stock?",
]

def main():
    router = Router()
    answerer = Answerer()
    with Neo4jClient() as client:
        embedder = Embedder()
        store = VectorStore(embedder)
        tools = ToolRegistry(client, store)

        for question in QUESTIONS:
            print(f"\nQ: {question}")
            mode = router.decide_mode(question)
            tool_names = router.select_tools(mode)
            print(f"Mode: {mode} | Tools: {tool_names}")

            # Try to generate and execute cypher if graph mode
            graph_results = []
            vector_results = []
            cypher_used = None

            if "generate_cypher" in tool_names:
                cypher_result = tools.generate_cypher(question)
                if cypher_result.success:
                    cypher_used = cypher_result.data["cypher"]
                    query_result = tools.query_neo4j(cypher_used)
                    if query_result.success:
                        graph_results = query_result.data

            if "search_vector_db" in tool_names:
                vector_result = tools.search_vector_db(question)
                if vector_result.success:
                    vector_results = vector_result.data

            output = answerer.generate_answer(
                question=question,
                mode=mode,
                graph_results=graph_results,
                vector_results=vector_results,
                cypher=cypher_used,
                tools_used=tool_names,
            )
            print(f"A: {output.answer[:300]}...")

if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Write `README.md`**

```markdown
# Neo4j GraphRAG Agent

A GraphRAG agent that converts enterprise-style documents into a Neo4j knowledge graph and answers questions through hybrid graph and vector retrieval.

## Project Highlights

This project demonstrates:
- **Ontology modeling** for enterprise documents (Module, API, Role, Permission, Workflow, Step, ErrorCode)
- **Neo4j-based knowledge graph** construction from unstructured docs
- **Template-based text2cypher** for structured reasoning (no LLM API required)
- **Hybrid GraphRAG** combining graph queries and FAISS vector retrieval
- **Agent tool calling** with automatic routing between graph, vector, and hybrid modes
- **Evaluation-ready** architecture with pytest test suite

## Architecture

```
User Query
    ↓
Agent Router (Rule-based intent classification)
    ↓
Template Text2Cypher / FAISS Vector Search / Hybrid
    ↓
Neo4j Graph Query + Text Evidence
    ↓
Evidence Fusion + Answer Generation
    ↓
Structured Answer with Citations
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+

### 1. Clone and Setup

```bash
cd neo4j-graphrag-agent
pip install -e ".[dev]"
```

### 2. Start Neo4j and API

```bash
docker compose up -d
```

- Neo4j Browser: http://localhost:7474 (login: neo4j / graphragdemo)
- API Docs: http://localhost:8000/docs

### 3. Build the Knowledge Graph

```bash
python examples/build_graph.py
```

Or via API:
```bash
curl -X POST http://localhost:8000/graph/build \
  -H "Content-Type: application/json" \
  -d '{"docs_dir": "data/raw_docs"}'
```

### 4. Ask Questions

```bash
curl -X POST http://localhost:8000/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which APIs are available in the procurement module?", "mode": "hybrid"}'
```

Or via CLI:
```bash
graphrag ask "Which APIs are available in the procurement module?"
```

## Demo Questions

| Question | Expected Mode | Why GraphRAG Wins |
|---|---|---|
| Which APIs are available in the procurement module? | graph | Exact API list from graph |
| Which roles can approve purchase orders? | graph | Role-Permission chain traversal |
| What are the steps from purchase request to inventory receiving? | graph | Workflow step chain via `NEXT_STEP` |
| Why does attachment upload fail? | hybrid | Error code + documentation |
| Which modules are involved in purchase-to-inventory conversion? | graph | Cross-module relationship query |

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Web API | FastAPI |
| Graph DB | Neo4j |
| Vector DB | FAISS |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| CLI | Typer |
| Testing | pytest |
| Deployment | Docker Compose |

## Project Structure

```
neo4j-graphrag-agent/
├── data/raw_docs/          # Sample ERP documents
├── src/graphrag_agent/
│   ├── ingestion/          # Document loading
│   ├── ontology/           # Schema definition
│   ├── extraction/         # Rule-based entity/relation extraction
│   ├── graph/              # Neo4j client + loader + safety
│   ├── retrieval/          # Chunking + Embedding + FAISS
│   ├── text2cypher/        # Intent classifier + Cypher templates
│   ├── agent/              # Router + Tools + Answerer
│   ├── api/                # FastAPI application
│   └── cli.py              # CLI commands
├── tests/                  # pytest test suite
└── examples/               # Demo scripts
```

## Testing

```bash
pytest tests/ -v
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/graph/build` | POST | Build graph from documents |
| `/search/vector` | POST | Vector search |
| `/cypher/generate` | POST | Generate Cypher from question |
| `/graph/query` | POST | Execute safe Cypher query |
| `/agent/ask` | POST | GraphRAG question answering |

## Resume Description

**Neo4j GraphRAG Agent** | Python, Neo4j, Cypher, FAISS, FastAPI, Docker
- Built a GraphRAG agent that converts enterprise-style documents into a Neo4j knowledge graph and answers questions through hybrid graph and vector retrieval.
- Designed an ontology covering modules, business objects, APIs, roles, permissions, workflows, and error codes.
- Implemented template-based text2cypher, safe Cypher execution, FAISS vector search, and evidence fusion for structured enterprise QA.
- Delivered a Docker Compose deployment with FastAPI backend and comprehensive pytest test suite.
```

- [ ] **Step 4: Run all tests one final time**

```bash
cd /Users/harryyu/neo4j-graphrag-agent
pytest tests/ -v --tb=short
```

Expected: All tests PASS (except potential integration tests that require Neo4j, which should be skipped or mocked)

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: complete MVP with sample docs, demos, and README"
```

---

## Spec Coverage Check

| Spec Requirement | Task |
|---|---|
| 文档导入 (Markdown, TXT, JSON) | Task 2 |
| Ontology (Entity/Relation Types) | Task 3 |
| 规则抽取 (Rule-based) | Task 4 |
| Neo4j 写入 + 安全查询 | Task 5 |
| 向量检索 (FAISS + sentence-transformers) | Task 6 |
| Template Text2Cypher | Task 7 |
| Agent 工具 (Router + Tools + Answerer) | Task 8 |
| FastAPI + CLI | Task 9 |
| Docker Compose | Task 1 |
| 测试问题设计 | Task 10 (README) |
| 对比展示 | Task 10 (README) |

## Placeholder Scan

✅ No TBD, TODO, or vague requirements in any task.

## Type Consistency

- `Document` model used consistently across ingestion, extraction, chunking
- `Entity` / `Relation` models used in extraction, ontology, graph loader
- `ToolResult` / `AnswerOutput` used in agent module
- `Neo4jClient` context manager used consistently

---
