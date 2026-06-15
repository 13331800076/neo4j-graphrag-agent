from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Document(BaseModel):
    doc_id: str = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title")
    source: str = Field(..., description="File path or source identifier")
    text: str = Field(..., description="Document content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extra metadata")

    class Config:
        frozen = False
