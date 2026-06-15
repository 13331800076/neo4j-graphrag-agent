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
