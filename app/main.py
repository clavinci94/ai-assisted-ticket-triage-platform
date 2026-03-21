from fastapi import FastAPI

from app.infrastructure.persistence.db import Base, engine
from app.interfaces.api.routes.admin import router as admin_router
from app.interfaces.api.routes.tickets import router as tickets_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-assisted Requirements & Ticket Triage Platform",
    version="0.1.0",
)

app.include_router(tickets_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
