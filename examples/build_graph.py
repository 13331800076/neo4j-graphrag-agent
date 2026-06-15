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
