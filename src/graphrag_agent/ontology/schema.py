from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class EntityType(str, Enum):
    MODULE = "Module"
    BUSINESS_OBJECT = "BusinessObject"
    API = "API"
    ROLE = "Role"
    PERMISSION = "Permission"
    WORKFLOW = "Workflow"
    STEP = "Step"
    ERROR_CODE = "ErrorCode"
    DOCUMENT = "Document"
    CHUNK = "Chunk"


class RelationType(str, Enum):
    BELONGS_TO = "BELONGS_TO"
    USES_API = "USES_API"
    REQUIRES_PERMISSION = "REQUIRES_PERMISSION"
    HAS_STEP = "HAS_STEP"
    NEXT_STEP = "NEXT_STEP"
    RELATED_TO = "RELATED_TO"
    DEFINED_IN = "DEFINED_IN"
    CAUSES = "CAUSES"
    SOLVED_BY = "SOLVED_BY"


class Entity(BaseModel):
    id: str = Field(..., description="Unique entity identifier")
    type: EntityType = Field(..., description="Entity type")
    name: str = Field(..., description="Human-readable name")
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_doc_id: Optional[str] = Field(None, description="Source document id")

    class Config:
        frozen = False


class Relation(BaseModel):
    id: str = Field(..., description="Unique relation identifier")
    type: RelationType = Field(..., description="Relation type")
    source_id: str = Field(..., description="Source entity id")
    target_id: str = Field(..., description="Target entity id")
    properties: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        frozen = False


class OntologySchema(BaseModel):
    entity_types: List[EntityType] = Field(default_factory=lambda: list(EntityType))
    relation_types: List[RelationType] = Field(default_factory=lambda: list(RelationType))

    def validate_entity(self, entity: Entity) -> bool:
        return entity.type in self.entity_types

    def validate_relation(self, relation: Relation) -> bool:
        return relation.type in self.relation_types
