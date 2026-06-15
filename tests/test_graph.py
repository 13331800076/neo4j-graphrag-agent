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
