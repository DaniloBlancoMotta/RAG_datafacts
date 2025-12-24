from typing import List

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ..., min_length=3, description="Quais as estratégias para automação de empresas sugerido pela Red Hat"
    )


class Source(BaseModel):
    source: str
    content_snippet: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: List[Source]
    confidence: str
    latency_ms: float
