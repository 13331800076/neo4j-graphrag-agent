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
