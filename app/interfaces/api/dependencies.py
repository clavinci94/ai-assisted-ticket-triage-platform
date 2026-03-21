from sqlalchemy.orm import Session

from app.infrastructure.persistence.db import SessionLocal
from app.infrastructure.persistence.sqlite_ticket_repository import SQLiteTicketRepository


def get_repository() -> SQLiteTicketRepository:
    session: Session = SessionLocal()
    return SQLiteTicketRepository(session=session)
