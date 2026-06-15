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
