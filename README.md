# Capstone Project: AI-assisted Requirements & Ticket Triage Platform


# AI-assisted Requirements & Ticket Triage Platform

Eine end-to-end Capstone-Plattform für intelligente Ticket-Erfassung, AI-gestützte Triage, menschliche Review, Team-Zuweisung, Analytics und Audit-Trail.

## Überblick

In vielen Teams werden eingehende Tickets, Incidents, Support-Anfragen und Anforderungen manuell gesichtet, kategorisiert und priorisiert. Das kostet Zeit, führt zu Inkonsistenzen und erschwert Transparenz über Entscheidungen, Verantwortlichkeiten und den Bearbeitungsstatus.

Dieses Projekt löst genau dieses Problem mit einer modernen, durchgängigen Plattform:

- Tickets erfassen
- AI-basierte Triage-Vorschläge erzeugen
- menschliche Review ermöglichen
- Tickets Teams zuweisen
- operative Kennzahlen visualisieren
- Ticket-Historie und Audit-Events nachvollziehbar speichern

Das System kombiniert klassische Machine-Learning-Verfahren mit einer strukturierten FastAPI-Backend-Architektur und einem React-Frontend mit Dashboard- und Detailansichten.

---

## Ziel des Projekts

Das Ziel ist **nicht nur** automatische Klassifikation, sondern eine **praktisch nutzbare Human-in-the-Loop-Triage-Plattform**, die:

- nachvollziehbar ist
- reviewbar ist
- auditierbar ist
- operativ nutzbar ist
- lokal einfach lauffähig ist
- eine saubere Grundlage für spätere Produktiv-Reife bietet

Der Fokus liegt auf einer realistischen Workflow-Unterstützung für Requirements, Bugs, Support-Anfragen und operative Tickets.

---

## Hauptfunktionen

### 1. Ticket Intake

Tickets können mit folgenden Feldern erfasst werden:

- `title`
- `description`
- `reporter`
- `source`

### 2. AI-assisted Triage

Das Backend analysiert Tickets mit:

- TF-IDF
- Multinomial Naive Bayes

und erzeugt unter anderem:

- vorhergesagte Kategorie
- vorhergesagte Priorität
- Zusammenfassung
- vorgeschlagenes Team
- empfohlener nächster Schritt
- Modell-Metadaten

### 3. Human Review

AI-Vorschläge können manuell geprüft und bestätigt oder angepasst werden:

- finale Kategorie
- finale Priorität
- finales Team
- Review-Kommentar
- Annahme oder Ablehnung der AI-Empfehlung

### 4. Assignment Workflow

Tickets können Teams zugewiesen werden mit:

- `assigned_team`
- `assigned_by`
- `assignment_note`

### 5. Dashboard Analytics

Das Dashboard stellt operative und Management-Metriken dar, zum Beispiel:

- Gesamtzahl Tickets
- Anzahl triagiert / reviewed / assigned
- Statusverteilung
- Kategorieverteilung
- Prioritätsverteilung
- Review Funnel
- AI Acceptance Rate
- Needs Attention
- Recent Activity

### 6. Ticket History / Audit Trail

Für jedes Ticket werden zentrale Events historisiert, zum Beispiel:

- Ticket erstellt
- AI-Triage abgeschlossen
- Review gespeichert
- Assignment gespeichert
- Status geändert

Dadurch ist der Ticket-Lebenszyklus nachvollziehbar und auditierbar.

### 7. Polished Frontend UX

Das Frontend bietet:

- Dashboard mit KPI-Karten
- Analytics-Charts mit Recharts
- Ticket-Detailseite
- Toast Notifications
- bessere Loading States
- bessere Empty States
- konsistentere Detail-UX
- Timeline-/History-Darstellung in der Detailseite

---

## Technologie-Stack

### Backend

- FastAPI
- SQLite
- SQLAlchemy
- Clean-Architecture-artige Struktur
- TF-IDF + Multinomial Naive Bayes

### Frontend

- React
- Vite
- React Router
- Axios
- Recharts

---

## Architektur

Das Projekt ist in klar getrennte Schichten organisiert:

- **Domain**: Entitäten, Enums, Regeln
- **Application**: Use Cases, DTOs, Ports
- **Infrastructure**: Datenbank, Persistence, AI-Klassifizierer
- **Interfaces**: API-Routes, Schemas, Mapper

Diese Struktur macht die Business-Logik besser wartbar und reduziert die Kopplung zwischen Framework und Kernlogik.

---

## Ticket Lifecycle

Ein Ticket durchläuft aktuell diese Stati:

1. `new`
2. `triaged`
3. `reviewed`
4. `assigned`

Diese Stati werden im Backend, in der Detailseite und in den Analytics verwendet.

---

## Projektstruktur

```text
ai-assisted-ticket-triage-platform/
├── app/
│   ├── application/
│   ├── domain/
│   ├── infrastructure/
│   ├── interfaces/
│   └── main.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   └── pages/
│   └── package.json
├── tests/
├── triage.db
├── requirements.txt
└── README.md
````

---

## API-Endpunkte

### Ticket-Endpunkte

* `GET /tickets`
* `GET /tickets/{ticket_id}`
* `GET /tickets/analytics`
* `POST /tickets/triage`
* `POST /tickets/decision`
* `POST /tickets/assign`

### Sonstige Endpunkte

* `GET /health`

---

## Beispiel: API-Nutzung

### Ticket erstellen und triagieren

```bash
curl -X POST "http://127.0.0.1:8000/tickets/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Checkout failure in production",
    "description": "Users cannot complete checkout after payment redirect.",
    "reporter": "claudio",
    "source": "internal"
  }'
```

### Review speichern

```bash
curl -X POST "http://127.0.0.1:8000/tickets/decision" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "REPLACE_WITH_TICKET_ID",
    "final_category": "bug",
    "final_priority": "high",
    "final_team": "engineering-team",
    "accepted_ai_suggestion": true,
    "review_comment": "Confirmed by reviewer.",
    "reviewed_by": "claudio"
  }'
```

### Assignment speichern

```bash
curl -X POST "http://127.0.0.1:8000/tickets/assign" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "REPLACE_WITH_TICKET_ID",
    "assigned_team": "engineering-team",
    "assigned_by": "claudio",
    "assignment_note": "Escalated to backend squad."
  }'
```

### Dashboard Analytics abrufen

```bash
curl "http://127.0.0.1:8000/tickets/analytics"
```

---

## Lokales Setup

### Voraussetzungen

Empfohlen:

* Python 3.11+ oder kompatibel
* Node.js 18+
* npm
* virtuelle Python-Umgebung

### 1. Repository klonen

```bash
git clone https://github.com/clavinci94/ai-assisted-ticket-triage-platform.git
cd ai-assisted-ticket-triage-platform
```

### 2. Backend einrichten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Backend starten

```bash
uvicorn app.main:app --reload
```

Backend läuft standardmäßig auf:

```text
http://127.0.0.1:8000
```

### 4. Frontend einrichten

```bash
cd frontend
npm install
```

### 5. Frontend starten

```bash
npm run dev
```

Frontend läuft standardmäßig auf:

```text
http://127.0.0.1:5173
```

### 6. Frontend-Umgebungsvariable

Das Frontend verwendet standardmäßig:

```js
import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000"
```

Optional kann im Ordner `frontend/` eine `.env` angelegt werden:

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000' > frontend/.env
```

---

## Tests und Validierung

### Backend-Tests

```bash
pytest -q
```

Abgedeckte Kernbereiche:

* Triage-Endpunkt
* Review-Status-Update
* Assignment-Status-Update
* Dashboard-Analytics-Endpunkt
* Ticket-History / Audit-Events
* Priority Rules
* zentrale Use-Case-Logik

### Frontend Production Build

```bash
cd frontend
npm run build
```

---

## UI-Überblick

### Dashboard

Das Dashboard enthält:

* Executive-/Hero-Header
* KPI-Karten
* Analytics-Charts
* Management-Metriken
* Review Funnel
* AI Acceptance Chart
* Needs Attention Panel
* Recent Activity Panel
* Ticket-Erstellung

### Ticket Detail Page

Die Detailseite enthält:

* Ticket-Metadaten
* AI-Empfehlungsübersicht
* Review-Workflow
* Assignment-Workflow
* Loading States
* Empty States
* Toast Notifications
* History & Audit Timeline

---

## Machine-Learning-Ansatz

Dieses Projekt nutzt bewusst einen leichten, nachvollziehbaren ML-Ansatz statt eines großen LLM-Stacks.

### Verwendetes Modell

* TF-IDF
* Multinomial Naive Bayes

### Vorteile für dieses Projekt

* schnell lokal ausführbar
* verständlich erklärbar
* gute Grundlage für klassische Textklassifikation
* leicht reproduzierbar
* sinnvoll für eine Capstone-Arbeit

### Einschränkungen

* weniger flexibel als moderne Transformer-/LLM-Ansätze
* Ergebnisqualität hängt stark von den Trainingsdaten ab
* Explainability ist vorhanden, aber begrenzt
* für echte Produktion wären weitere Maßnahmen nötig

---

## Auditability & Human-in-the-Loop

Ein zentrales Designziel dieses Projekts ist **kontrollierte Unterstützung statt Black-Box-Automation**.

Deshalb enthält das System:

* explizite Review-Schritte
* explizite Assignments
* serverseitige Analytics
* Ticket-History / Audit-Events
* nachverfolgbaren Lifecycle

Das ist besonders wichtig in realistischen Business-Umgebungen, in denen Verantwortlichkeit und Nachvollziehbarkeit zählen.

---

## Aktueller Reifegrad

Dieses Projekt ist ein **starker, funktional abgeschlossener Capstone-Stand** mit:

* funktionsfähigem Backend
* funktionsfähigem Frontend
* AI-Triage
* Dashboard-Analytics
* Detailseiten-Politur
* History / Audit Trail
* Tests
* erfolgreichem Production Build

Es ist damit deutlich mehr als eine reine Demo, aber noch nicht vollständig produktionsreif im Enterprise-Sinn.

---

## Bekannte Grenzen / mögliche Erweiterungen

Mögliche nächste Ausbaustufen:

* Authentifizierung und Autorisierung
* Rollenmodell / RBAC
* Alembic-Migrationen
* PostgreSQL statt SQLite
* Docker / Containerisierung
* CI/CD
* Monitoring / Logging / Alerting
* Modellversionierung
* Explainability-Oberflächen
* Drift Monitoring
* Bulk Actions
* Rate Limiting
* Code Splitting zur Reduktion der Bundle-Größenwarnung

---

## Für wen dieses Projekt geeignet ist

Dieses Projekt eignet sich als:

* Capstone-/Bachelor-/Master-Demonstrator
* Portfolio-Projekt
* Referenz für FastAPI + React + ML Integration
* Beispiel für Human-in-the-Loop Triage-Workflows
* Grundlage für ein späteres produktionsnahes System

---

## Quick Start

Backend starten:

```bash
git clone https://github.com/clavinci94/ai-assisted-ticket-triage-platform.git
cd ai-assisted-ticket-triage-platform

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend in einem zweiten Terminal:

```bash
cd frontend
npm install
npm run dev
```

Tests:

```bash
pytest -q
```

Frontend-Build:

```bash
cd frontend
npm run build
```

---

## Finaler Projektstatus

Aktueller Stand:

* Backend implementiert
* Frontend implementiert
* AI-Triage integriert
* Dashboard Analytics serverseitig
* Ticket Detail Page poliert
* History / Audit Events implementiert
* Tests grün
* Build grün
* Repository getaggt mit `capstone-complete`

---

## Autor

Erstellt von Claudio im Rahmen eines Capstone-Projekts.

Repository:

* `https://github.com/clavinci94/ai-assisted-ticket-triage-platform`



