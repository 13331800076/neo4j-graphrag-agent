from pydantic import BaseModel
from typing import Any, Optional, Dict
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
