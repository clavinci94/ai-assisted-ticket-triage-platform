from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.infrastructure.persistence.db import Base, engine
from app.interfaces.api.routes.admin import router as admin_router
from app.interfaces.api.routes.tickets import router as tickets_router

Base.metadata.create_all(bind=engine)
from app.infrastructure.persistence.db import ensure_ticket_columns

ensure_ticket_columns()

app = FastAPI(
    title="AI-assisted Requirements & Ticket Triage Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
