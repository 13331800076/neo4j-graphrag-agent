from pydantic import BaseModel, Field
from typing import List
from graphrag_agent.ontology.schema import Entity, Relation


class ExtractionResult(BaseModel):
    entities: List[Entity] = Field(default_factory=list)
    relations: List[Relation] = Field(default_factory=list)
