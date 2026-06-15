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
