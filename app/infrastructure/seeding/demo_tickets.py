"""Reusable demo-data seeder for the retrieval-augmented triage demo.

Exposes one side-effect function, ``seed(replace: bool) -> int``, and the
``DEMO_TICKETS`` list of realistic Bank-IT support cases across six
departments. Used both by:

* ``scripts/seed_demo_tickets.py`` — CLI wrapper for local runs
* ``POST /admin/seed-demo`` — HTTP endpoint for populating cloud deploys
  without shell access (and without letting DB credentials leave Render).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from app.infrastructure.persistence.db import (
    Base,
    SessionLocal,
    engine,
    ensure_ticket_columns,
)
from app.infrastructure.persistence.models import TicketRecordModel

SEED_PREFIX = "DEMO-"


def _ts(days_ago: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago)


DEMO_TICKETS: list[dict] = [
    # -------------------------- VPN / Network --------------------------
    {
        "id": "DEMO-0001",
        "title": "VPN Citrix Workspace verbindet nicht",
        "description": (
            "Mitarbeiter aus dem Retail-Backoffice meldet wiederholte "
            "Verbindungsabbrüche beim VPN-Login via Citrix Workspace am Windows-Arbeitsplatz."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["vpn", "citrix", "windows"],
    },
    {
        "id": "DEMO-0002",
        "title": "Citrix startet auf Mac nicht mehr",
        "description": (
            "Nach macOS-Update (Sonoma) schlägt der VPN-Login mit Fehler 500 fehl. "
            "Betroffen sind drei Teammitglieder im Audit-Bereich."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["vpn", "citrix", "macos"],
    },
    {
        "id": "DEMO-0003",
        "title": "WLAN im Konferenzraum 2B instabil",
        "description": (
            "Verbindung zum Konferenz-WLAN bricht ca. alle 15 Minuten ab, betrifft alle Geräte im Raum."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "network-team",
        "tags": ["wlan", "hardware"],
    },
    # -------------------------- User Services --------------------------
    {
        "id": "DEMO-0004",
        "title": "Passwort-Reset für SAP FI",
        "description": "Benutzer aus Finanzbuchhaltung hat sein SAP-Passwort vergessen. Kein AD-Zugriff möglich.",
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["password", "sap"],
    },
    {
        "id": "DEMO-0005",
        "title": "Neuer Mitarbeiter — Zugänge einrichten",
        "description": (
            "Onboarding für Junior-Kreditanalyst. Benötigt Mailbox, AD-Account, "
            "VPN-Zertifikat, Zugriff auf Laufwerk K: und Moody's-Rating-Portal."
        ),
        "department": "Bank-IT Support",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["onboarding", "access"],
    },
    {
        "id": "DEMO-0006",
        "title": "Berechtigung für Laufwerk K: fehlt",
        "description": "Kollegin kann das gemeinsame Laufwerk K: nicht öffnen seit Rollen-Umbenennung.",
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "user-services",
        "tags": ["access", "fileshare"],
    },
    # -------------------------- Hardware --------------------------
    {
        "id": "DEMO-0007",
        "title": "Drucker Etage 3 offline",
        "description": "Etagendrucker (Kyocera TASKalfa) reagiert seit heute Morgen nicht mehr.",
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["printer", "hardware"],
    },
    {
        "id": "DEMO-0008",
        "title": "Monitor zeigt kein Bild mehr",
        "description": "Externer Monitor am Laptop-Dock funktioniert nach Kabeltausch nicht mehr.",
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "hardware-team",
        "tags": ["hardware", "monitor"],
    },
    {
        "id": "DEMO-0009",
        "title": "Headset Bluetooth verbindet sich nicht",
        "description": "Dienst-Headset Jabra verbindet sich nicht mehr mit Teams auf Windows-Laptop.",
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["hardware", "headset"],
    },
    # -------------------------- Payments Ops --------------------------
    {
        "id": "DEMO-0010",
        "title": "SEPA-Datei wird nicht verarbeitet",
        "description": (
            "Hochgeladene SEPA-XML-Datei wird im Payments-Portal nicht gebucht. "
            "Keine sichtbare Fehlermeldung."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sepa", "payments"],
    },
    {
        "id": "DEMO-0011",
        "title": "SWIFT-MT103 wird zurückgewiesen",
        "description": "Auslandsüberweisung per SWIFT MT103 wird mit Reject-Code 72 zurückgewiesen.",
        "department": "Payments Operations",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["swift", "payments"],
    },
    {
        "id": "DEMO-0012",
        "title": "IBAN-Validierung schlägt fehl",
        "description": (
            "Gültige belgische IBAN wird im Kundenportal als ungültig markiert. "
            "Vermutlich Checksummen-Regel veraltet."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "payments-ops",
        "tags": ["iban", "validation"],
    },
    # -------------------------- Digital Channels --------------------------
    {
        "id": "DEMO-0013",
        "title": "Mobile App — Login-Schleife nach Update",
        "description": (
            "Nach App-Update auf Version 4.12 landen einige User in Login-Schleife. Betrifft iOS wie Android."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "login"],
    },
    {
        "id": "DEMO-0014",
        "title": "Online-Banking zeigt alten Kontostand",
        "description": (
            "Kontostand im Online-Banking bleibt für 24h stehen, trotz Buchungen. Cache-Problem im Frontend?"
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "online-banking-team",
        "tags": ["online-banking", "cache"],
    },
    {
        "id": "DEMO-0015",
        "title": "Push-Benachrichtigungen kommen nicht an",
        "description": "Firebase-Token wird nicht mehr erneuert, Push kommt in der App nicht an.",
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "mobile-app-team",
        "tags": ["push", "firebase"],
    },
    # -------------------------- Risk & Compliance --------------------------
    {
        "id": "DEMO-0016",
        "title": "KYC-Export für BaFin-Audit benötigt",
        "description": (
            "Compliance benötigt anonymisierten Export der KYC-Daten Q1/2026 für den anstehenden BaFin-Audit."
        ),
        "department": "Risk & Compliance",
        "final_category": "requirement",
        "final_priority": "high",
        "final_team": "compliance-ops",
        "tags": ["compliance", "kyc", "audit"],
    },
    {
        "id": "DEMO-0017",
        "title": "AML-Alert Engine übersieht Transaktionen",
        "description": (
            "Stichproben zeigen, dass die AML-Alert-Engine Transaktionen > 15k EUR "
            "in bestimmten Konstellationen nicht flaggt."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "aml-team",
        "tags": ["aml", "compliance"],
    },
    # -------------------------- Retail / Corporate --------------------------
    {
        "id": "DEMO-0018",
        "title": "Kunde will Tagesgeldkonto eröffnen",
        "description": (
            "Privatkunde fragt über Web-Formular nach Konditionen und Eröffnung eines Tagesgeldkontos."
        ),
        "department": "Retail Banking",
        "final_category": "question",
        "final_priority": "low",
        "final_team": "retail-frontoffice",
        "tags": ["retail", "tagesgeld"],
    },
    {
        "id": "DEMO-0019",
        "title": "Firmenkunde — Kreditrahmen erhöhen",
        "description": "Bestehender Corporate-Kunde bittet um Erhöhung des Betriebsmittelkredits um 250k EUR.",
        "department": "Corporate Banking",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "corporate-relationship",
        "tags": ["corporate", "credit-line"],
    },
    {
        "id": "DEMO-0020",
        "title": "Baufinanzierung — Unterlagen unvollständig",
        "description": (
            "Bei Immobilienfinanzierung fehlen die letzten zwei Gehaltsabrechnungen "
            "und der aktuelle Grundbuchauszug."
        ),
        "department": "Lending Services",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "lending-ops",
        "tags": ["lending", "baufi"],
    },
]


def _serialize_tags(tags: list[str]) -> str | None:
    if not tags:
        return None
    return json.dumps(tags)


def _build_row(spec: dict, days_ago: int) -> TicketRecordModel:
    return TicketRecordModel(
        id=spec["id"],
        title=spec["title"],
        description=spec["description"],
        reporter="demo-seed",
        source="internal",
        department=spec["department"],
        category=spec["final_category"],
        priority=spec["final_priority"],
        team=spec["final_team"],
        tags=_serialize_tags(spec.get("tags", [])),
        sla_breached=False,
        status="reviewed",
        final_category=spec["final_category"],
        final_priority=spec["final_priority"],
        final_team=spec["final_team"],
        accepted_ai_suggestion=True,
        reviewed_by="demo-operator",
        analyzed_at=_ts(days_ago),
    )


def seed(replace: bool = False) -> dict:
    """Insert the demo corpus into the currently configured database.

    Returns a dict describing what happened, suitable for direct JSON
    return from an admin endpoint.
    """

    Base.metadata.create_all(bind=engine)
    ensure_ticket_columns()

    session = SessionLocal()
    inserted = 0
    deleted = 0
    try:
        if replace:
            deleted = (
                session.query(TicketRecordModel)
                .filter(TicketRecordModel.id.like(f"{SEED_PREFIX}%"))
                .delete(synchronize_session=False)
            )
            session.commit()

        existing_ids = {
            row[0]
            for row in session.query(TicketRecordModel.id)
            .filter(TicketRecordModel.id.like(f"{SEED_PREFIX}%"))
            .all()
        }

        for offset, spec in enumerate(DEMO_TICKETS):
            if spec["id"] in existing_ids:
                continue
            session.add(_build_row(spec, days_ago=(30 - offset)))
            inserted += 1
        session.commit()
    finally:
        session.close()

    return {
        "status": "ok",
        "deleted": deleted,
        "inserted": inserted,
        "total_demo_records": len(DEMO_TICKETS),
        "skipped_existing": len(DEMO_TICKETS) - inserted,
    }
