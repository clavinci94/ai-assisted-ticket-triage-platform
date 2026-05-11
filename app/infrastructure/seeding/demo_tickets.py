"""Reusable data seeder for the retrieval-augmented triage demo.

Exposes one side-effect function, ``seed(...)``, and the
``DEMO_TICKETS`` list of realistic Bank-IT support cases across six
departments. Used both by:

* ``scripts/seed_demo_tickets.py`` — CLI wrapper for local runs
* ``POST /admin/seed-demo`` — HTTP endpoint for populating cloud deploys
  without shell access (and without letting DB credentials leave Render).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import func

from app.infrastructure.persistence.db import (
    Base,
    SessionLocal,
    engine,
    ensure_ticket_columns,
)
from app.infrastructure.persistence.models import TicketEventModel, TicketRecordModel

SEED_PREFIX = "DEMO-"
HIST_PREFIX = "HIST-"
SEED_PREFIXES: tuple[str, ...] = (SEED_PREFIX, HIST_PREFIX)

# Title prefixes produced by the pytest e2e suite. Historically tests ran
# against the same DB as the demo, so these accumulated as visible "tickets"
# in the UI. Always safe to purge.
TEST_POLLUTION_TITLE_PREFIXES: tuple[str, ...] = (
    "WB-PAGE-CLAUDIO",
    "WB-VIEWS-CLAUDIO",
    "Workflow Close Test",
    "Workflow Comment Test",
    "Workflow Escalation Test",
    "LLM connectivity check",
)

# Status precedence when deduplicating non-demo rows that share a title:
# the more "advanced" the lifecycle, the more interesting the record.
_STATUS_RANK = {
    "closed": 5,
    "assigned": 4,
    "reviewed": 3,
    "triaged": 2,
    "new": 1,
}


def _ts(days_ago: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days_ago)


DEMO_TICKETS: list[dict] = [
    # -------------------------- VPN / Network --------------------------
    {
        "id": "DEMO-001",
        "title": "VPN Citrix Workspace verbindet nicht (Windows)",
        "description": (
            "Mitarbeiter aus dem Retail-Backoffice meldet wiederholte "
            "Verbindungsabbrüche beim VPN-Login via Citrix Workspace am Windows-Arbeitsplatz. "
            "Fehler tritt seit dem letzten Citrix-Update auf, Reconnect funktioniert nur sporadisch."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["vpn", "citrix", "windows"],
    },
    {
        "id": "DEMO-002",
        "title": "Citrix startet auf macOS Sonoma mit Fehler 500 nicht",
        "description": (
            "Nach macOS-Update (Sonoma 14.4) schlägt der VPN-Login mit Fehler 500 fehl. "
            "Betroffen sind drei Teammitglieder im Audit-Bereich, Windows-Kollegen sind nicht betroffen."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["vpn", "citrix", "macos"],
    },
    {
        "id": "DEMO-003",
        "title": "WLAN im Konferenzraum 2B alle 15 Minuten instabil",
        "description": (
            "Verbindung zum Konferenz-WLAN bricht ca. alle 15 Minuten ab, betrifft alle Geräte im Raum 2B. "
            "Andere Konferenzräume auf derselben Etage sind nicht betroffen — vermutlich Access-Point defekt."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "network-team",
        "tags": ["wlan", "hardware"],
    },
    # -------------------------- User Services --------------------------
    {
        "id": "DEMO-004",
        "title": "Passwort-Reset für SAP FI (Finanzbuchhaltung)",
        "description": (
            "Benutzer aus der Finanzbuchhaltung hat sein SAP-FI-Passwort vergessen und hat keinen AD-Zugriff mehr. "
            "Reset über Self-Service-Portal scheitert mit „Benutzer gesperrt“."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["password", "sap"],
    },
    {
        "id": "DEMO-005",
        "title": "Onboarding Junior-Kreditanalyst — Zugänge einrichten",
        "description": (
            "Onboarding für neue Junior-Kreditanalystin (Start am Montag). Benötigt Mailbox, AD-Account, "
            "VPN-Zertifikat, Zugriff auf Laufwerk K: (Kredit-Akten) und Moody's-Rating-Portal."
        ),
        "department": "Bank-IT Support",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["onboarding", "access"],
    },
    {
        "id": "DEMO-006",
        "title": "Berechtigung für Laufwerk K: nach Rollenwechsel weg",
        "description": (
            "Kollegin aus Compliance kann das gemeinsame Laufwerk K: nicht mehr öffnen, "
            "seit sie letzte Woche von „Compliance-Analyst“ auf „Compliance-Senior“ umbenannt wurde."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "user-services",
        "tags": ["access", "fileshare"],
    },
    # -------------------------- Hardware --------------------------
    {
        "id": "DEMO-007",
        "title": "Etagendrucker Kyocera (Etage 3) offline",
        "description": (
            "Etagendrucker Kyocera TASKalfa auf Etage 3 reagiert seit heute Morgen 08:00 nicht mehr. "
            "Display schwarz, keine Reaktion auf Tasten. Vermutlich Hardware-Defekt oder Netzteilausfall."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["printer", "hardware"],
    },
    {
        "id": "DEMO-008",
        "title": "Externer Monitor am Laptop-Dock zeigt kein Bild",
        "description": (
            "Externer Dell-Monitor am USB-C-Dock bleibt schwarz, auch nach Kabeltausch (HDMI und DisplayPort getestet). "
            "Laptop selbst funktioniert, Dock ist neu seit letzter Woche."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "hardware-team",
        "tags": ["hardware", "monitor"],
    },
    {
        "id": "DEMO-009",
        "title": "Jabra-Headset verbindet sich nicht mehr mit Teams",
        "description": (
            "Dienst-Headset Jabra Evolve2 65 verbindet sich nicht mehr via Bluetooth mit Microsoft Teams "
            "auf Windows-Laptop. Andere Bluetooth-Geräte funktionieren, in Teams selbst wird das Headset nicht erkannt."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["hardware", "headset"],
    },
    # -------------------------- Payments Ops --------------------------
    {
        "id": "DEMO-010",
        "title": "SEPA-XML-Datei wird im Payments-Portal nicht gebucht",
        "description": (
            "Hochgeladene SEPA-XML-Datei (pain.001.001.03) wird im Payments-Portal angenommen, "
            "aber nicht gebucht — keine sichtbare Fehlermeldung. Betroffen ist eine Sammelzahlung über 47 Aufträge."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sepa", "payments"],
    },
    {
        "id": "DEMO-011",
        "title": "SWIFT-MT103 wird mit Reject-Code 72 zurückgewiesen",
        "description": (
            "Auslandsüberweisung per SWIFT MT103 an US-Korrespondenzbank wird mit Reject-Code 72 zurückgewiesen. "
            "Empfänger-BIC und IBAN sind verifiziert, Betrag und Währung plausibel."
        ),
        "department": "Payments Operations",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["swift", "payments"],
    },
    {
        "id": "DEMO-012",
        "title": "Gültige belgische IBAN wird als ungültig markiert",
        "description": (
            "Im Kundenportal wird eine gültige belgische IBAN (BE…) als ungültig markiert — "
            "Checksumme passt laut externem IBAN-Rechner. Vermutlich Validierungsregel im Frontend veraltet."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "payments-ops",
        "tags": ["iban", "validation"],
    },
    # -------------------------- Digital Channels --------------------------
    {
        "id": "DEMO-013",
        "title": "Mobile App 4.12 — Login-Schleife nach Update (iOS & Android)",
        "description": (
            "Nach App-Update auf Version 4.12 landen einige User in einer Login-Schleife: "
            "nach Eingabe der PIN wird sie sofort wieder abgefragt. Betrifft iOS wie Android, "
            "ca. 5% der aktiven User laut Telemetrie."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "login"],
    },
    {
        "id": "DEMO-014",
        "title": "Online-Banking zeigt 24h-alten Kontostand trotz Buchungen",
        "description": (
            "Kontostand im Online-Banking bleibt für ca. 24h auf altem Stand, obwohl Buchungen "
            "im Kontoauszug korrekt erscheinen. Cache-Problem im Frontend wahrscheinlich, "
            "Hard-Refresh hilft aber nicht."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "online-banking-team",
        "tags": ["online-banking", "cache"],
    },
    {
        "id": "DEMO-015",
        "title": "Push-Benachrichtigungen kommen in der App nicht an",
        "description": (
            "Firebase-Token wird nach App-Restart nicht mehr erneuert, dadurch erreichen "
            "Push-Benachrichtigungen die Mobile App nicht. Backend-Logs zeigen erfolgreiche FCM-Calls, "
            "Geräte empfangen sie aber nicht."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "mobile-app-team",
        "tags": ["push", "firebase"],
    },
    # -------------------------- Risk & Compliance --------------------------
    {
        "id": "DEMO-016",
        "title": "KYC-Datenexport Q1/2026 für BaFin-Audit benötigt",
        "description": (
            "Compliance benötigt einen anonymisierten Export der KYC-Daten Q1/2026 "
            "für den anstehenden BaFin-Audit am 20.05. Format: CSV mit dokumentiertem Schema, "
            "Personenbezug pseudonymisiert."
        ),
        "department": "Risk & Compliance",
        "final_category": "requirement",
        "final_priority": "high",
        "final_team": "compliance-ops",
        "tags": ["compliance", "kyc", "audit"],
    },
    {
        "id": "DEMO-017",
        "title": "AML-Alert-Engine übersieht Transaktionen über 15k EUR",
        "description": (
            "Stichproben zeigen, dass die AML-Alert-Engine Transaktionen über 15.000 EUR "
            "in bestimmten Konstellationen (Korrespondenzbank + Drittland) nicht flaggt. "
            "Compliance-Risiko, schnelle Analyse durch AML-Team nötig."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "aml-team",
        "tags": ["aml", "compliance"],
    },
    # -------------------------- Retail / Corporate --------------------------
    {
        "id": "DEMO-018",
        "title": "Privatkunde fragt nach Tagesgeldkonto-Konditionen",
        "description": (
            "Privatkunde fragt über das Web-Formular nach Konditionen und Eröffnung eines Tagesgeldkontos "
            "(Anlagesumme ca. 50.000 EUR, Laufzeit offen). Rückruf gewünscht."
        ),
        "department": "Retail Banking",
        "final_category": "question",
        "final_priority": "low",
        "final_team": "retail-frontoffice",
        "tags": ["retail", "tagesgeld"],
    },
    {
        "id": "DEMO-019",
        "title": "Corporate-Kunde bittet um Erhöhung Betriebsmittelkredit (+250k)",
        "description": (
            "Bestehender Corporate-Kunde (Maschinenbau, seit 2014 bei uns) bittet um Erhöhung "
            "des Betriebsmittelkredits um 250.000 EUR. Aktueller Rahmen ausgeschöpft, "
            "Bilanz Q4/2025 liegt vor."
        ),
        "department": "Corporate Banking",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "corporate-relationship",
        "tags": ["corporate", "credit-line"],
    },
    {
        "id": "DEMO-020",
        "title": "Baufinanzierung — fehlende Gehaltsabrechnungen und Grundbuchauszug",
        "description": (
            "Bei Immobilienfinanzierung (Objekt in München, Volumen 620k EUR) fehlen "
            "die letzten zwei Gehaltsabrechnungen beider Antragsteller sowie der aktuelle Grundbuchauszug. "
            "Termin mit Notar steht in 10 Tagen."
        ),
        "department": "Lending Services",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "lending-ops",
        "tags": ["lending", "baufi"],
    },
]


HISTORICAL_TICKETS: list[dict] = [
    # ============== Cluster 1: VPN / Citrix / Konnektivität ==============
    {
        "id": "HIST-001",
        "title": "Citrix-Workspace verliert Verbindung im Home-Office",
        "description": (
            "Mitarbeiterin im Home-Office berichtet, dass Citrix Workspace nach 10–15 Minuten "
            "Inaktivität die Sitzung verliert. Reconnect funktioniert, ist aber störend bei Telefonaten."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "network-team",
        "tags": ["vpn", "citrix"],
    },
    {
        "id": "HIST-002",
        "title": "VPN-Profil nach Laptop-Tausch nicht mehr vorhanden",
        "description": (
            "Nach Tausch des Dienstlaptops fehlt das vorkonfigurierte VPN-Profil. Benutzer kann sich "
            "nicht ins interne Netz einwählen. Zertifikat wurde noch nicht ausgerollt."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["vpn", "laptop", "zertifikat"],
    },
    {
        "id": "HIST-003",
        "title": "Citrix-Login schlägt mit Fehler „Server nicht erreichbar“ fehl",
        "description": (
            "Mehrere User aus dem Zahlungsverkehrs-Team melden Citrix-Anmeldung mit Fehler "
            "„Server nicht erreichbar“. Ping auf Gateway funktioniert, vermutlich Storefront-Problem."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "network-team",
        "tags": ["citrix", "storefront"],
    },
    {
        "id": "HIST-004",
        "title": "WLAN-Roaming zwischen Stockwerken bricht ab",
        "description": (
            "Beim Wechsel zwischen Etage 4 und Etage 5 fällt das WLAN kurz aus. Teams-Calls werden "
            "unterbrochen. Vermutlich falsch konfiguriertes Roaming auf den Access-Points."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "network-team",
        "tags": ["wlan", "roaming"],
    },
    {
        "id": "HIST-005",
        "title": "VPN-Geschwindigkeit langsamer als 5 Mbit/s",
        "description": (
            "Kollege aus Audit klagt über extrem langsame VPN-Verbindung (< 5 Mbit/s) trotz "
            "100 Mbit/s Anschluss zu Hause. Speedtest außerhalb VPN zeigt volle Leistung."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "network-team",
        "tags": ["vpn", "performance"],
    },
    {
        "id": "HIST-006",
        "title": "MFA-Token funktioniert nach Handy-Wechsel nicht",
        "description": (
            "Nach Wechsel des Diensthandys lässt sich der MFA-Token nicht mehr in der Authenticator-App "
            "registrieren. Benutzer ist von VPN- und Citrix-Login ausgeschlossen."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["mfa", "authenticator", "vpn"],
    },
    {
        "id": "HIST-007",
        "title": "Konferenz-WLAN benötigt Gastzugang für externe Berater",
        "description": (
            "Externe Berater aus Wirtschaftsprüfungsgesellschaft benötigen für die kommende Woche "
            "Gast-WLAN-Zugang. 6 Personen, Internet-only, keine internen Ressourcen."
        ),
        "department": "Bank-IT Support",
        "final_category": "requirement",
        "final_priority": "low",
        "final_team": "network-team",
        "tags": ["wlan", "guest", "external"],
    },
    # ============== Cluster 2: Passwort / Account-Lockout ==============
    {
        "id": "HIST-008",
        "title": "AD-Konto nach 5 Fehlversuchen gesperrt",
        "description": (
            "Kollege hat sich nach Rückkehr aus dem Urlaub mehrfach mit altem Passwort angemeldet. "
            "AD-Konto ist gesperrt, Self-Service-Reset scheitert mit Fehler 0x80070569."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["password", "ad", "lockout"],
    },
    {
        "id": "HIST-009",
        "title": "Passwort-Reset für Bloomberg-Terminal benötigt",
        "description": (
            "Trader bittet um Reset des Bloomberg-Terminal-Passworts. Letzter Login vor 3 Wochen, "
            "B-Unit aktuell vorhanden, Token im Terminalraum."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["password", "bloomberg"],
    },
    {
        "id": "HIST-010",
        "title": "SSO-Login zum Intranet scheitert nach Domain-Wechsel",
        "description": (
            "Nach Migration des Benutzers in neue AD-Domäne funktioniert das SSO ins Intranet "
            "nicht mehr. Login-Seite wird angezeigt statt Auto-Login, manuelle Anmeldung klappt."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["sso", "intranet", "ad"],
    },
    {
        "id": "HIST-011",
        "title": "Service-Account-Passwort läuft nächste Woche ab",
        "description": (
            "Monitoring meldet bevorstehenden Ablauf des Service-Accounts svc-payments-prod. "
            "Rotation und Update der hinterlegten Konfigs (Vault, App-Pool) nötig vor Freitag."
        ),
        "department": "Bank-IT Support",
        "final_category": "requirement",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["password", "service-account", "rotation"],
    },
    {
        "id": "HIST-012",
        "title": "Benutzer kann Passwort nicht selbst zurücksetzen — Sicherheitsfragen vergessen",
        "description": (
            "Mitarbeiter erinnert sich nicht mehr an Antworten der Sicherheitsfragen und kann den "
            "Self-Service-Reset nicht abschließen. Identitätsprüfung über Vorgesetzten nötig."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["password", "self-service"],
    },
    {
        "id": "HIST-013",
        "title": "Outlook fragt ständig nach Passwort trotz korrekter Eingabe",
        "description": (
            "Outlook 2021 fragt alle paar Minuten nach dem Mailbox-Passwort, obwohl das Passwort "
            "korrekt ist. Tritt seit gestern Mittag bei mehreren Kollegen auf — vermutlich Token-Problem."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["outlook", "password", "token"],
    },
    {
        "id": "HIST-014",
        "title": "Zugang zu Risk-Engine nach Rollenänderung verloren",
        "description": (
            "Kollegin wurde von „Risk-Analyst“ zu „Senior Risk-Analyst“ befördert. Damit ist die "
            "Berechtigungsgruppe gewechselt, der Zugang zur Risk-Engine fehlt jetzt aber komplett."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["access", "risk-engine"],
    },
    # ============== Cluster 3: Hardware ==============
    {
        "id": "HIST-015",
        "title": "Multifunktionsdrucker scannt nicht in Mailbox",
        "description": (
            "Kyocera-Multifunktionsdrucker druckt einwandfrei, das Scannen in Mailbox schlägt jedoch "
            "mit „SMTP-Authentifizierung fehlgeschlagen“ fehl. Konfiguration nach Mail-Server-Update prüfen."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["printer", "scan", "smtp"],
    },
    {
        "id": "HIST-016",
        "title": "Laptop fährt nicht mehr hoch — schwarzer Bildschirm",
        "description": (
            "Dell Latitude 7440 zeigt nach Drücken des Power-Buttons nur einen schwarzen Bildschirm. "
            "LED leuchtet, Lüfter dreht kurz, dann nichts mehr. Vermutlich Mainboard oder RAM."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "hardware-team",
        "tags": ["laptop", "hardware-defekt"],
    },
    {
        "id": "HIST-017",
        "title": "Zweiter Monitor wird nach Dock-Tausch nicht erkannt",
        "description": (
            "Nach Tausch des USB-C-Docks erkennt Windows nur einen der beiden angeschlossenen Monitore. "
            "Treiber-Update auf Dock-Firmware geprüft, Problem besteht weiter."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "hardware-team",
        "tags": ["monitor", "dock", "hardware"],
    },
    {
        "id": "HIST-018",
        "title": "Tastatur einzelne Tasten ohne Funktion",
        "description": (
            "Auf der Logitech-Tastatur des Kollegen funktionieren die Tasten „E“ und „R“ nicht mehr. "
            "Andere Tasten reagieren normal, Reinigung und Tausch des USB-Ports geprüft."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["tastatur", "hardware"],
    },
    {
        "id": "HIST-019",
        "title": "Headset-Mikrofon wird in Teams nicht erkannt",
        "description": (
            "Jabra-Headset wird vom System erkannt, das Mikrofon erscheint in Teams aber nicht "
            "als Eingabegerät. Treiber neu installiert, Privatsphäre-Einstellung ist auf „Zulassen“."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "hardware-team",
        "tags": ["headset", "teams", "mikrofon"],
    },
    {
        "id": "HIST-020",
        "title": "Smartcard-Leser am Arbeitsplatz defekt",
        "description": (
            "Smartcard-Leser am Arbeitsplatz Compliance-Backoffice reagiert nicht mehr. Karte wird "
            "weder gelesen noch ausgeworfen. Vermutlich Defekt — Austausch nötig."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "hardware-team",
        "tags": ["smartcard", "hardware"],
    },
    {
        "id": "HIST-021",
        "title": "Drucker auf Etage 5 druckt unleserliche Seiten",
        "description": (
            "Drucker druckt seit heute Morgen verschwommene und gestreifte Seiten. Toner-Kassette "
            "ist laut Display noch zu 40% gefüllt. Vermutlich Drum-Einheit am Ende der Lebensdauer."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["printer", "drum"],
    },
    {
        "id": "HIST-022",
        "title": "Webcam am Notebook funktioniert nicht in Teams",
        "description": (
            "Integrierte Webcam des HP EliteBook wird in Windows-Kamera-App korrekt angezeigt, "
            "in Teams jedoch nicht ausgewählt werden. Treiber aktuell, Teams-Client neu installiert."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "low",
        "final_team": "hardware-team",
        "tags": ["webcam", "teams"],
    },
    # ============== Cluster 4: SAP / Finance Applications ==============
    {
        "id": "HIST-023",
        "title": "SAP FI startet mit Fehler „Tabelle T001 nicht gefunden“",
        "description": (
            "Nach Patch-Wochenende meldet SAP FI beim Start „Tabelle T001 nicht gefunden“. "
            "Betrifft nur den DEV-Mandanten, PROD läuft. Vermutlich Transport-Order nicht eingespielt."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["sap", "fi", "transport"],
    },
    {
        "id": "HIST-024",
        "title": "SAP-GUI hängt beim Wechsel zwischen Mandanten",
        "description": (
            "Nach Update auf SAP GUI 8.00 friert die Anwendung beim Mandantenwechsel ein. "
            "Reproduzierbar bei allen Anwendern im Finance-Team."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["sap", "gui"],
    },
    {
        "id": "HIST-025",
        "title": "Buchungstext in SAP wird nach 60 Zeichen abgeschnitten",
        "description": (
            "Buchungstexte > 60 Zeichen werden in der Liste abgeschnitten. Detailansicht zeigt den "
            "vollständigen Text, die Listenansicht wirkt jedoch verwirrend. Layout-Variante anpassen."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "low",
        "final_team": "user-services",
        "tags": ["sap", "ux"],
    },
    {
        "id": "HIST-026",
        "title": "Berechtigungsfehler in SAP S/4HANA bei T-Code FB60",
        "description": (
            "Kollege aus Kreditorenbuchhaltung erhält bei Aufruf von FB60 „Sie haben keine Berechtigung "
            "für Aktivität 03 in Buchungskreis 0001“. Rolle ZFI_KREDITOR ist zugewiesen."
        ),
        "department": "Bank-IT Support",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["sap", "s4hana", "berechtigung"],
    },
    {
        "id": "HIST-027",
        "title": "Moody's-Rating-Portal lädt keine neuen Reports",
        "description": (
            "Im Moody's-Rating-Portal werden seit gestern Abend keine neuen Reports mehr angezeigt. "
            "Login funktioniert, Liste aber leer. API-Status-Page von Moody's prüfen."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["moodys", "rating", "external-api"],
    },
    {
        "id": "HIST-028",
        "title": "Excel-Plugin „Smartview“ verbindet nicht zur Hyperion-Datenbank",
        "description": (
            "Smartview-Plugin in Excel meldet „Connection failed“ beim Verbinden mit Hyperion. "
            "Tritt nach Office-Update auf, andere Plugins funktionieren."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "user-services",
        "tags": ["excel", "hyperion", "smartview"],
    },
    {
        "id": "HIST-029",
        "title": "Datev-Export der Buchhaltung schlägt fehl",
        "description": (
            "Monatlicher Datev-Export aus der Finanzbuchhaltung scheitert mit „Encoding error: invalid "
            "characters in row 4271“. Verdächtig: Sonderzeichen in Lieferantenname aus letzter Woche."
        ),
        "department": "Bank-IT Support",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "user-services",
        "tags": ["datev", "export", "encoding"],
    },
    # ============== Cluster 5: SEPA / SWIFT / Payments ==============
    {
        "id": "HIST-030",
        "title": "SEPA-Lastschrift wird mit Reason-Code AC04 zurückgegeben",
        "description": (
            "Sammellastschrift über 230 Aufträge wird teilweise mit AC04 (Kundenkonto aufgelöst) "
            "zurückgegeben. Stammdaten-Abgleich mit CRM nötig, vermutlich veraltete IBANs."
        ),
        "department": "Payments Operations",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sepa", "lastschrift", "rejection"],
    },
    {
        "id": "HIST-031",
        "title": "SWIFT MT202 für Liquiditätsausgleich nicht angekommen",
        "description": (
            "Liquiditätsausgleich um 14:30 per SWIFT MT202 an unsere DZ-Bank-Korrespondenz wurde "
            "im SWIFT-Monitor als „sent“ markiert, ist aber nicht beim Empfänger angekommen."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "payments-ops",
        "tags": ["swift", "mt202", "liquidität"],
    },
    {
        "id": "HIST-032",
        "title": "Instant-Payment (SCT Inst) wird nicht innerhalb 10 Sekunden bestätigt",
        "description": (
            "Mehrere Instant-Payments (SCT Inst) überschreiten die 10-Sekunden-Frist und fallen "
            "auf normale SCT zurück. Betrifft ca. 8% der Transaktionen seit heute Morgen."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sct-inst", "instant-payment"],
    },
    {
        "id": "HIST-033",
        "title": "TARGET2-Verbindung in der Nacht abgebrochen",
        "description": (
            "Nightly-Settlement TARGET2 wurde um 02:14 Uhr durch Verbindungsabbruch unterbrochen. "
            "Manuelle Wiederaufnahme um 02:31 erfolgreich, Settlement vollständig abgeschlossen."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "payments-ops",
        "tags": ["target2", "settlement", "nightly"],
    },
    {
        "id": "HIST-034",
        "title": "BIC-Validierung lehnt gültigen Schweizer SIC-Code ab",
        "description": (
            "Im Payments-Portal wird ein gültiger Schweizer SIC-Code als ungültiger BIC markiert. "
            "Validierungsregel scheint reine BIC-Codes anzunehmen, kein SIC-Mapping vorhanden."
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "payments-ops",
        "tags": ["bic", "sic", "validation"],
    },
    {
        "id": "HIST-035",
        "title": "Cut-off-Zeit für SEPA-Überweisungen wurde nicht eingehalten",
        "description": (
            "Drei Großüberweisungen wurden um 17:01 Uhr eingereicht, knapp nach Cut-off (17:00). "
            "Kunde besteht auf Same-Day-Settlement, Eskalation an Compliance-Team."
        ),
        "department": "Payments Operations",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sepa", "cut-off", "settlement"],
    },
    {
        "id": "HIST-036",
        "title": "Devisenkurs-Feed liefert veraltete EUR/USD-Quotierung",
        "description": (
            "FX-Feed zeigt EUR/USD-Kurs vom Vortag-Close, obwohl Markt seit 9 Uhr offen ist. "
            "Reuters-API-Status grün, internes Mapping fehlerhaft?"
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["fx", "reuters", "feed"],
    },
    {
        "id": "HIST-037",
        "title": "Erstattungsantrag (SEPA Recall) wird nicht generiert",
        "description": (
            "Recall-Antrag für versehentlich versandte SEPA-Überweisung lässt sich im Payments-Portal "
            "nicht erstellen — Button reagiert nicht, keine Fehlermeldung. Frontend-Bug?"
        ),
        "department": "Payments Operations",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "payments-ops",
        "tags": ["sepa", "recall", "frontend"],
    },
    # ============== Cluster 6: Online-Banking / Mobile App ==============
    {
        "id": "HIST-038",
        "title": "Online-Banking-Session läuft nach 5 Minuten ab",
        "description": (
            "Mehrere Kunden beschweren sich, dass die Online-Banking-Session bereits nach 5 Minuten "
            "Inaktivität abläuft. Soll-Wert laut Doku: 15 Minuten. Vermutlich Session-Config falsch."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "online-banking-team",
        "tags": ["online-banking", "session"],
    },
    {
        "id": "HIST-039",
        "title": "Mobile App stürzt beim Öffnen der Überweisungs-Maske ab",
        "description": (
            "Auf Android 14 stürzt die Mobile App reproduzierbar ab, wenn die Überweisungs-Maske "
            "geöffnet wird. iOS nicht betroffen. Crashlytics-Logs zeigen NullPointer in IBAN-Eingabe."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "android", "crash"],
    },
    {
        "id": "HIST-040",
        "title": "QR-Login funktioniert mit neuer iOS-Version nicht",
        "description": (
            "Nach iOS-Update 17.4 schlägt der QR-Login in der Mobile App fehl. Kamera öffnet, "
            "QR-Code wird gescannt, App meldet aber „Verbindung fehlgeschlagen“."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "ios", "qr-login"],
    },
    {
        "id": "HIST-041",
        "title": "Online-Banking-Login zeigt CAPTCHA dauerhaft an",
        "description": (
            "User aus Asien-Pazifik berichten, dass beim Login dauerhaft ein CAPTCHA gezeigt wird, "
            "auch nach korrekter Eingabe. Vermutlich Fraud-Engine markiert IP-Range als verdächtig."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "online-banking-team",
        "tags": ["online-banking", "captcha", "fraud"],
    },
    {
        "id": "HIST-042",
        "title": "PDF-Download von Kontoauszug bleibt bei 0% stehen",
        "description": (
            "Bei einigen Kunden bleibt der Download des PDF-Kontoauszugs bei 0% stehen. Browser-Konsole "
            "zeigt Timeout bei /api/statements/{id}/pdf. Backend-Logs zeigen lange Generierungszeiten."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "online-banking-team",
        "tags": ["pdf", "kontoauszug", "performance"],
    },
    {
        "id": "HIST-043",
        "title": "Dauerauftrag lässt sich in Mobile App nicht löschen",
        "description": (
            "In der Mobile App reagiert der „Dauerauftrag löschen“-Button nicht. Web-Version "
            "funktioniert, Mobile-Workaround nötig oder Hotfix für nächsten Release einplanen."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "dauerauftrag"],
    },
    {
        "id": "HIST-044",
        "title": "Push-TAN wird im Online-Banking nicht akzeptiert",
        "description": (
            "Push-TAN-Verfahren liefert TAN an die App, beim Eingeben im Online-Banking wird "
            "„TAN ungültig oder abgelaufen“ gemeldet. Vermutlich Zeit-Drift zwischen Servern."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "online-banking-team",
        "tags": ["pushtan", "online-banking", "auth"],
    },
    {
        "id": "HIST-045",
        "title": "Apple-Pay-Verknüpfung im Onboarding scheitert",
        "description": (
            "Im Onboarding-Flow der Mobile App schlägt der Schritt „Karte mit Apple Pay verknüpfen“ "
            "mit Fehler 4042 fehl. Apple-Wallet-Provisioning prüft Karten-BIN, evtl. Whitelist fehlt."
        ),
        "department": "Digital Channels",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "mobile-app-team",
        "tags": ["mobile-app", "apple-pay", "onboarding"],
    },
    # ============== Cluster 7: Compliance / KYC / AML ==============
    {
        "id": "HIST-046",
        "title": "Identifikations-Dokument im KYC-Portal wird nicht hochgeladen",
        "description": (
            "Compliance-Mitarbeiter kann Identifikations-Dokumente > 5 MB nicht ins KYC-Portal "
            "hochladen. Frontend bricht ohne Fehlermeldung ab. Soll-Limit laut Doku 10 MB."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "high",
        "final_team": "compliance-ops",
        "tags": ["kyc", "upload"],
    },
    {
        "id": "HIST-047",
        "title": "AML-Alert für hochrisiko-Land Iran nicht ausgelöst",
        "description": (
            "Stichprobe zeigt Transaktion mit Korrespondenzbank in Teheran ohne AML-Alert. "
            "Hochrisiko-Länderliste prüfen, ggf. Mapping-Tabelle aktualisieren."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "aml-team",
        "tags": ["aml", "high-risk", "alert"],
    },
    {
        "id": "HIST-048",
        "title": "PEP-Screening liefert false-positives für gängige Namen",
        "description": (
            "PEP-Screening flaggt gängige Namen (z.B. „Hans Müller“) als möglichen PEP-Treffer. "
            "Schwellenwert der Namens-Ähnlichkeit zu niedrig konfiguriert."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "medium",
        "final_team": "compliance-ops",
        "tags": ["pep", "screening", "false-positive"],
    },
    {
        "id": "HIST-049",
        "title": "Quartalsbericht für FINMA vorbereiten",
        "description": (
            "Compliance benötigt Aggregat der gemeldeten AML-Verdachtsfälle Q1/2026 für FINMA-Report. "
            "Standardformat, Abgabe in zwei Wochen."
        ),
        "department": "Risk & Compliance",
        "final_category": "requirement",
        "final_priority": "high",
        "final_team": "compliance-ops",
        "tags": ["finma", "reporting", "aml"],
    },
    {
        "id": "HIST-050",
        "title": "Sanktionslisten-Update nicht automatisch eingespielt",
        "description": (
            "OFAC-Update vom 12.04. wurde nicht automatisch ins Sanktionslisten-System eingespielt. "
            "Cron-Job läuft, Log zeigt aber Permission-Fehler beim Schreiben."
        ),
        "department": "Risk & Compliance",
        "final_category": "bug",
        "final_priority": "critical",
        "final_team": "aml-team",
        "tags": ["sanctions", "ofac", "cron"],
    },
    {
        "id": "HIST-051",
        "title": "GDPR-Löschantrag eines Kunden bearbeiten",
        "description": (
            "Privatkunde fordert Löschung aller personenbezogenen Daten nach Art. 17 DSGVO. "
            "Aufbewahrungsfristen aus dem Bankrecht prüfen, Antwort innerhalb 30 Tagen."
        ),
        "department": "Risk & Compliance",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "compliance-ops",
        "tags": ["gdpr", "löschantrag"],
    },
    {
        "id": "HIST-052",
        "title": "MaRisk-Audit Vorbereitung: Zugriffe auf Risikomanagement-Systeme",
        "description": (
            "Internal Audit benötigt Liste aller User mit Schreibzugriff auf das Risikomanagement-System "
            "der letzten 12 Monate. Export inkl. Rollenwechsel."
        ),
        "department": "Risk & Compliance",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "compliance-ops",
        "tags": ["marisk", "audit", "access-review"],
    },
    # ============== Cluster 8: Retail / Corporate / Lending ==============
    {
        "id": "HIST-053",
        "title": "Privatkunde bittet um Limiterhöhung Kreditkarte",
        "description": (
            "Bestandskunde (seit 2018) bittet um Limiterhöhung auf seiner Gold-Kreditkarte von "
            "5.000 EUR auf 10.000 EUR, plant Auslandsreise. Kreditrating-Check ausstehend."
        ),
        "department": "Retail Banking",
        "final_category": "requirement",
        "final_priority": "low",
        "final_team": "retail-frontoffice",
        "tags": ["kreditkarte", "limit"],
    },
    {
        "id": "HIST-054",
        "title": "Kunde meldet verlorene EC-Karte",
        "description": (
            "Privatkunde meldet telefonisch verlorene EC-Karte. Sperrung sofort über Hotline veranlasst, "
            "Ersatzkarte beauftragt, Lieferzeit 5 Werktage."
        ),
        "department": "Retail Banking",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "retail-frontoffice",
        "tags": ["ec-karte", "sperrung"],
    },
    {
        "id": "HIST-055",
        "title": "Anfrage zur Eröffnung eines Wertpapierdepots",
        "description": (
            "Neukunde fragt nach Konditionen für Wertpapierdepot mit aktivem Trading (ca. 50 Trades/Jahr). "
            "Interesse an US-Aktien und ETFs. Rückruf durch Wertpapier-Spezialist gewünscht."
        ),
        "department": "Retail Banking",
        "final_category": "question",
        "final_priority": "low",
        "final_team": "retail-frontoffice",
        "tags": ["wertpapier", "depot"],
    },
    {
        "id": "HIST-056",
        "title": "Corporate-Kunde fragt nach Termingeschäft (FX-Forward)",
        "description": (
            "Maschinenbau-Kunde plant USD-Zahlung in 3 Monaten und möchte FX-Forward 500k USD. "
            "Treasury-Desk einbeziehen für Quotierung."
        ),
        "department": "Corporate Banking",
        "final_category": "question",
        "final_priority": "medium",
        "final_team": "corporate-relationship",
        "tags": ["fx", "forward", "treasury"],
    },
    {
        "id": "HIST-057",
        "title": "Kreditlinie für Saisongeschäft verlängern",
        "description": (
            "Corporate-Kunde aus dem Einzelhandel bittet um Verlängerung der saisonalen Kreditlinie "
            "(Weihnachtsgeschäft 2026). Bisheriger Rahmen 1,2 Mio EUR. Risiko-Vote nötig."
        ),
        "department": "Corporate Banking",
        "final_category": "requirement",
        "final_priority": "medium",
        "final_team": "corporate-relationship",
        "tags": ["corporate", "kreditlinie"],
    },
    {
        "id": "HIST-058",
        "title": "Bauträger meldet Verzögerung bei Immobilien-Projektfinanzierung",
        "description": (
            "Bauträger meldet bauseitige Verzögerung um 3 Monate. Tranchen-Abruf aus der "
            "Projektfinanzierung muss angepasst werden, Covenants prüfen."
        ),
        "department": "Lending Services",
        "final_category": "support",
        "final_priority": "high",
        "final_team": "lending-ops",
        "tags": ["projektfinanzierung", "covenants"],
    },
    {
        "id": "HIST-059",
        "title": "Privatkunde fragt nach Sondertilgung Baufinanzierung",
        "description": (
            "Privatkunde mit laufender Baufinanzierung möchte einmalig 25.000 EUR sondertilgen. "
            "Vertraglich erlaubt sind 5% pro Jahr, Berechnung Restschuld nach Tilgung benötigt."
        ),
        "department": "Lending Services",
        "final_category": "question",
        "final_priority": "low",
        "final_team": "lending-ops",
        "tags": ["baufi", "sondertilgung"],
    },
    {
        "id": "HIST-060",
        "title": "Konsumkredit-Antrag mit unvollständigem Einkommensnachweis",
        "description": (
            "Antrag auf Konsumkredit 18.000 EUR liegt vor, Antragsteller hat aber nur zwei statt drei "
            "Gehaltsabrechnungen eingereicht. Nachfrage an Vertrieb, Bearbeitung gestoppt."
        ),
        "department": "Lending Services",
        "final_category": "support",
        "final_priority": "medium",
        "final_team": "lending-ops",
        "tags": ["konsumkredit", "einkommensnachweis"],
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


def _delete_tickets(session, ticket_ids: list[str]) -> int:
    if not ticket_ids:
        return 0
    (
        session.query(TicketEventModel)
        .filter(TicketEventModel.ticket_id.in_(ticket_ids))
        .delete(synchronize_session=False)
    )
    deleted = (
        session.query(TicketRecordModel)
        .filter(TicketRecordModel.id.in_(ticket_ids))
        .delete(synchronize_session=False)
    )
    return int(deleted)


def _purge_test_pollution(session) -> int:
    """Delete tickets whose title matches a known pytest e2e fixture prefix."""

    from sqlalchemy import or_

    if not TEST_POLLUTION_TITLE_PREFIXES:
        return 0

    filters = [TicketRecordModel.title.like(f"{prefix}%") for prefix in TEST_POLLUTION_TITLE_PREFIXES]
    rows = session.query(TicketRecordModel.id).filter(or_(*filters)).all()
    ids = [row[0] for row in rows]
    return _delete_tickets(session, ids)


def _not_seed_filter():
    """SQLAlchemy filter that excludes every seeded prefix (DEMO-/HIST-)."""

    from sqlalchemy import and_

    return and_(*[~TicketRecordModel.id.like(f"{p}%") for p in SEED_PREFIXES])


def _dedupe_non_demo_titles(session) -> int:
    """For every non-seed title that appears multiple times, keep one row.

    Preference order: highest status rank (closed > assigned > reviewed >
    triaged > new), then most recent analyzed_at, then most recent id.
    Seeded rows (DEMO-* / HIST-*) are never touched.
    """

    duplicate_titles_q = (
        session.query(TicketRecordModel.title)
        .filter(_not_seed_filter())
        .group_by(TicketRecordModel.title)
        .having(func.count(TicketRecordModel.id) > 1)
    )
    duplicate_titles = [row[0] for row in duplicate_titles_q.all()]

    if not duplicate_titles:
        return 0

    ids_to_delete: list[str] = []
    for title in duplicate_titles:
        candidates = (
            session.query(TicketRecordModel)
            .filter(TicketRecordModel.title == title)
            .filter(_not_seed_filter())
            .all()
        )
        if len(candidates) <= 1:
            continue

        def _sort_key(record: TicketRecordModel) -> tuple:
            rank = _STATUS_RANK.get((record.status or "").lower(), 0)
            analyzed = record.analyzed_at or datetime.min.replace(tzinfo=UTC)
            return (rank, analyzed, record.id)

        candidates.sort(key=_sort_key, reverse=True)
        # Keep candidates[0], delete the rest
        ids_to_delete.extend(c.id for c in candidates[1:])

    return _delete_tickets(session, ids_to_delete)


def _insert_corpus(
    session,
    catalog: list[dict],
    *,
    existing_ids: set[str],
    days_offset: int,
) -> int:
    """Insert any catalog entries not yet present. Returns inserted count."""

    inserted = 0
    for offset, spec in enumerate(catalog):
        if spec["id"] in existing_ids:
            continue
        session.add(_build_row(spec, days_ago=max(1, days_offset - offset)))
        inserted += 1
    return inserted


def seed(
    replace: bool = False,
    purge_test_pollution: bool = False,
    dedupe_non_demo: bool = False,
) -> dict:
    """Insert the demo + historical corpus into the currently configured database.

    Parameters
    ----------
    replace:
        Delete existing seeded rows (DEMO-* and HIST-*) before reseeding.
        Makes the operation idempotent against the curated catalog.
    purge_test_pollution:
        Delete rows whose title matches a known pytest e2e fixture
        (``WB-PAGE-CLAUDIO``, ``WB-VIEWS-CLAUDIO``, ``Workflow * Test``).
    dedupe_non_demo:
        For non-seed titles that exist more than once, keep one
        representative row and delete the rest.

    Returns a dict describing what happened, suitable for direct JSON
    return from an admin endpoint.
    """

    Base.metadata.create_all(bind=engine)
    ensure_ticket_columns()

    session = SessionLocal()
    demo_inserted = 0
    hist_inserted = 0
    deleted = 0
    purged = 0
    deduped = 0
    try:
        if purge_test_pollution:
            purged = _purge_test_pollution(session)
            session.commit()

        if dedupe_non_demo:
            deduped = _dedupe_non_demo_titles(session)
            session.commit()

        if replace:
            existing_seed_ids = []
            for prefix in SEED_PREFIXES:
                existing_seed_ids.extend(
                    row[0]
                    for row in session.query(TicketRecordModel.id)
                    .filter(TicketRecordModel.id.like(f"{prefix}%"))
                    .all()
                )
            deleted = _delete_tickets(session, existing_seed_ids)
            session.commit()

        existing_ids = {
            row[0]
            for row in session.query(TicketRecordModel.id)
            .filter(
                TicketRecordModel.id.like(f"{SEED_PREFIX}%") | TicketRecordModel.id.like(f"{HIST_PREFIX}%")
            )
            .all()
        }

        demo_inserted = _insert_corpus(
            session,
            DEMO_TICKETS,
            existing_ids=existing_ids,
            days_offset=30,
        )
        # Historical tickets get older timestamps so the demo set still
        # looks like the "freshest" reviewed corpus on the workbench.
        hist_inserted = _insert_corpus(
            session,
            HISTORICAL_TICKETS,
            existing_ids=existing_ids,
            days_offset=180,
        )
        session.commit()
    finally:
        session.close()

    total_catalog = len(DEMO_TICKETS) + len(HISTORICAL_TICKETS)
    inserted = demo_inserted + hist_inserted
    return {
        "status": "ok",
        "deleted": deleted,
        "inserted": inserted,
        "inserted_demo": demo_inserted,
        "inserted_historical": hist_inserted,
        "purged_test_pollution": purged,
        "deduplicated": deduped,
        "total_demo_records": len(DEMO_TICKETS),
        "total_historical_records": len(HISTORICAL_TICKETS),
        "skipped_existing": total_catalog - inserted,
    }
