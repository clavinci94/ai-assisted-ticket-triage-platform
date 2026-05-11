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
    inserted_demo: int = 0
    inserted_historical: int = 0
    purged_test_pollution: int = 0
    deduplicated: int = 0
    skipped_existing: int
    total_demo_records: int
    total_historical_records: int = 0
    indexed_tickets: int | None = None
    message: str
