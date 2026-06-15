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
