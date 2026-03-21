from fastapi import FastAPI

from app.interfaces.api.routes.tickets import router as tickets_router

app = FastAPI(
    title="AI-assisted Requirements & Ticket Triage Platform",
    version="0.1.0",
)

app.include_router(tickets_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
