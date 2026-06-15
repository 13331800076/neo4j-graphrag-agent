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
