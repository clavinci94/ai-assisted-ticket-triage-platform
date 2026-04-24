from pydantic import BaseModel


class RetrainResponse(BaseModel):
    status: str
    message: str
    model_path: str


class RebuildRagResponse(BaseModel):
    status: str
    indexed_tickets: int
    minimum_corpus_size: int
    message: str
