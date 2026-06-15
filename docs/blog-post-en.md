# Building a Neo4j GraphRAG Agent from Enterprise Documents: A Practical Guide

> A production-ready portfolio project demonstrating knowledge graph modeling, GraphRAG, and agent engineering — without any LLM API key.

## The Problem with Vanilla RAG

If you've built RAG systems before, you've probably hit this wall: **vector similarity works great for factual questions, but fails miserably for structured reasoning.**

Consider these enterprise questions:
- "Which APIs are available in the procurement module?" → Semantic search might return paragraphs mentioning "API" and "procurement", but miss the complete list.
- "What are the steps from purchase request to inventory receiving?" → Chunk boundaries often cut off the workflow chain.
- "Which roles can approve purchase orders?" → Requires traversing Role → Permission → Workflow relationships.

The root cause is simple: **unstructured documents contain implicit relationships and processes that pure semantic similarity cannot capture.**

## The GraphRAG Approach

```
Enterprise Documents → Ontology Design → Knowledge Graph → Graph Reasoning → Vector Retrieval → Evidence Fusion → Agent Answer
```

The key difference: we explicitly model entities and relationships into a graph, allowing queries to traverse chains (`HAS_STEP` → `NEXT_STEP` → `REQUIRES_PERMISSION`) rather than relying on semantic approximation.

## Architecture Overview

```
User Query
    ↓
Agent Router (Rule-based Intent Classification)
    ↓
Template Text2Cypher / FAISS Vector Search / Hybrid
    ↓
Neo4j Graph Query + Text Evidence
    ↓
Evidence Fusion + Answer Generation
    ↓
Structured Answer with Citations
```

## Ontology Design: The Foundation of GraphRAG

Why does ontology design matter? **Entity types and relationship types determine what questions you can answer.**

### Entity Types (10)

| Type | Examples | Source in Document |
|---|---|---|
| Module | Procurement, Inventory | Document title |
| BusinessObject | PurchaseOrder, InventoryItem | Explicit lists |
| API | createPurchaseOrder, queryInventory | Code blocks |
| Role | Procurement Clerk, Manager | Role sections |
| Permission | PURCHASE_CREATE, APPROVE | Permission descriptions |
| Workflow | Procurement Workflow | Workflow headers |
| Step | Submit Request, Manager Approval | Numbered lists |
| ErrorCode | ATT_001 | Error code tables |
| Document | procurement.md | Source document |
| Chunk | procurement_chunk_0 | Text chunks |

### Relationship Types (9)

| Relation | Example | Use Case |
|---|---|---|
| BELONGS_TO | API → Module | Query APIs by module |
| USES_API | BusinessObject → API | Find APIs for objects |
| REQUIRES_PERMISSION | Role → Permission | Role-permission chains |
| HAS_STEP | Workflow → Step | List workflow steps |
| NEXT_STEP | Step → Step | Traverse process order |
| RELATED_TO | Module → Module | Cross-module queries |
| DEFINED_IN | API → Document | Source tracking |
| CAUSES | ErrorCode → Cause | Error diagnosis |
| SOLVED_BY | ErrorCode → Solution | Troubleshooting |

## Key Technical Decisions

### 1. Rule-Based Extraction (No LLM)

We deliberately avoided LLM-based entity extraction in v1 for three reasons:
- **Reproducibility**: Same documents → same graph, every time
- **Zero cost**: No API keys needed, runs entirely locally
- **Testability**: Every rule has a corresponding unit test

```python
# Extract Module from H1
re.search(r"^#\s+(.+)\s+Module", text, re.MULTILINE | re.IGNORECASE)

# Extract APIs from bullet lists
re.match(r"-\s+`?([^`]+)`?\s*-\s*(.+)", line)

# Extract Role-Permission pairs
re.match(r"-\s+(.+?)\s*-\s*Requires?\s+(.+)\s+permission", line, re.IGNORECASE)

# Extract Workflow Steps from numbered lists
re.match(r"\d+\.\s+(.+)", line)
```

### 2. Template-Based Text2Cypher (No LLM)

Instead of using LLM to generate Cypher (black box, expensive, risky), we use a two-layer approach:

**Layer 1: Intent Classification** (rule-based)
```python
class QuestionIntent(Enum):
    API_BY_MODULE = "api_by_module"
    ROLES_BY_PERMISSION = "roles_by_permission"
    WORKFLOW_STEPS = "workflow_steps"
    ERROR_SOLUTION = "error_solution"
    BUSINESS_OBJECT_RELATION = "business_object_relation"
```

**Layer 2: Template Matching**
```cypher
// API_BY_MODULE
MATCH (m:Entity {type: 'Module', name: 'Procurement'})
<-[:RELATION {type: 'BELONGS_TO'}]-(api:Entity {type: 'API'})
RETURN api.name AS api_name, api.properties.description AS description

// WORKFLOW_STEPS
MATCH (wf:Entity {type: 'Workflow', name: 'Procurement Workflow'})
-[:RELATION {type: 'HAS_STEP'}]->(s:Entity {type: 'Step'})
OPTIONAL MATCH (s)-[:RELATION {type: 'NEXT_STEP'}]->(next:Entity {type: 'Step'})
RETURN s.name AS step_name, s.properties.order AS step_order, next.name AS next_step
ORDER BY s.properties.order
```

**Benefits**: Fast, zero-cost, 100% predictable, read-only by design.

### 3. Cypher Safety Validation

```python
FORBIDDEN_KEYWORDS = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "CSV", "apoc", "gds", "dbms",
}

def validate_read_only(cypher: str) -> bool:
    upper = cypher.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in upper:
            raise CypherSafetyError(f"Forbidden keyword: {keyword}")
    return True
```

### 4. FAISS + sentence-transformers for Local Vector Search

Using `all-MiniLM-L6-v2` (384 dimensions), running entirely locally:

```python
class VectorStore:
    def __init__(self, embedder: Embedder, dimension: int = 384):
        self.index = faiss.IndexFlatIP(dimension)
        # ...
```

**Why FAISS over Milvus/Pinecone?** The goal is "clone and run locally in one command". FAISS is the lightest option for an MVP.

### 5. Agent Tool Routing

```python
class Router:
    def decide_mode(self, question: str) -> str:
        intent = self.classifier.classify(question)
        if intent in {API_BY_MODULE, WORKFLOW_STEPS, ROLES_BY_PERMISSION}:
            return "graph"
        if intent == ERROR_SOLUTION:
            return "hybrid"
        return "vector"
```

**Three modes**:
- **graph**: Structured questions → text2cypher + Neo4j
- **vector**: Semantic questions → FAISS retrieval
- **hybrid**: Error troubleshooting → both graph + vector

## Demo Questions Proving GraphRAG Advantage

| Question | Mode | Why Vanilla RAG Fails |
|---|---|---|
| Which APIs are in the procurement module? | graph | Semantic search doesn't guarantee coverage |
| Which roles can approve purchase orders? | graph | Requires Role → Permission chain traversal |
| What are the steps from request to receiving? | graph | Needs `NEXT_STEP` relationship traversal |
| Why does attachment upload fail? | hybrid | Needs structured ErrorCode → Cause → Solution |
| Which modules are involved in purchase-to-inventory? | graph | Cross-module relationship query |

## Project Structure

```
neo4j-graphrag-agent/
├── data/raw_docs/          # 5 sample ERP documents
├── src/graphrag_agent/
│   ├── ingestion/          # Document loading
│   ├── ontology/           # Schema (10 entities + 9 relations)
│   ├── extraction/         # Rule-based extraction
│   ├── graph/              # Neo4j client + safety + loader
│   ├── retrieval/          # Chunking + Embedding + FAISS
│   ├── text2cypher/        # Intent classifier + Cypher templates
│   ├── agent/              # Router + Tools + Answerer
│   ├── api/                # FastAPI (6 endpoints)
│   └── cli.py              # Typer CLI
├── tests/                  # 27 pytest tests
├── examples/               # 3 demo scripts
└── docker-compose.yml      # Neo4j + API one-click start
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Start Neo4j + API
docker compose up -d

# Build knowledge graph
python examples/build_graph.py

# Ask questions
graphrag ask "Which APIs are available in the procurement module?"
```

## The Philosophy of v1: Intentional Subtraction

This project deliberately avoids:
- ❌ LLM entity extraction → ✅ Rule-based (reproducible, testable)
- ❌ LLM text2cypher → ✅ Template matching (zero-cost, predictable)
- ❌ LLM answer generation → ✅ Rule-based evidence fusion (testable)
- ❌ Milvus/Pinecone → ✅ FAISS (lightweight, local)
- ❌ Frontend UI → ✅ FastAPI + CLI (focus on core capabilities)

**The goal**: Make "knowledge graph modeling" and "agent engineering" shine, rather than building a feature-bloated half-baked product.

## What This Project Demonstrates

For interviewers and recruiters, this project proves you can:
- **Model enterprise knowledge** into structured ontologies
- **Engineer graph databases** (Neo4j, Cypher, batch imports)
- **Design safe query interfaces** (read-only validation, schema constraints)
- **Build retrieval systems** (vector + graph hybrid)
- **Orchestrate agent tools** (routing, evidence fusion, structured output)
- **Deliver production-ready code** (tests, Docker, API, CLI)

## Future Extensions

If you want to iterate further:
1. **LLM-based text2cypher**: Add LLM layer on top of templates for flexible queries
2. **LLM extraction**: Complement rule-based extraction with LLM for edge cases
3. **Multi-hop reasoning**: Support "Which roles can approve inventory-related purchases?" (Role → Permission → Workflow → Step → Module)
4. **Evaluation framework**: Design Recall@k, MRR metrics comparing Vector vs Graph vs Hybrid
5. **Web UI**: Add Gradio/Streamlit interface

## Conclusion

This project's purpose is not "building a chatbot" — it's **proving you can extract enterprise knowledge from unstructured documents, model it into structured graphs, design safe query interfaces, and orchestrate these capabilities into a reliable question-answering system through agent tooling.**

When an interviewer asks "What RAG projects have you built?", you can open Neo4j Browser and show them the graph, then walk through the text2cypher generation process. That's much more convincing than "I used LangChain with a vector store."

**GitHub**: https://github.com/13331800076/neo4j-graphrag-agent

## References

- [Neo4j GraphRAG Python SDK](https://neo4j.com/docs/neo4j-graphrag-python/current/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [sentence-transformers](https://www.sbert.net/)
- [Microsoft GraphRAG](https://microsoft.github.io/graphrag/)
