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


class SeedDemoResponse(BaseModel):
    status: str
    deleted: int
    inserted: int
    skipped_existing: int
    total_demo_records: int
    indexed_tickets: int | None = None
    message: str
