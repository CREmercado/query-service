from pydantic import BaseModel
from typing import Optional, List
from .config import QDRANT_COLLECTION

class RagQueryRequest(BaseModel):
    query: str
    useExpansion: Optional[bool] = False
    topK: Optional[int] = None
    topN: Optional[int] = None
    collection: Optional[str] = QDRANT_COLLECTION

class TopDoc(BaseModel):
    id: str
    rerank: float
    payload: dict

class RagQueryResponse(BaseModel):
    answer: str
    model_used: str
    topDocs: List[TopDoc]
    context: str

class HealthCheck(BaseModel):
    status: str
    ollama: str
    qdrant: str