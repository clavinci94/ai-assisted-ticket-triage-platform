const OVERVIEW_CARDS = [
  {
    eyebrow: "Startpunkt",
    title: "Was die Plattform leistet",
    description:
      "Die Ticket-Triage-Plattform bündelt Erfassung, KI-Empfehlung, Prüfung, Zuweisung und Nachverfolgung in einem klaren Ablauf.",
    helper: "Ziel: schneller entscheiden und sauber weiterleiten",
  },
  {
    eyebrow: "Bedienung",
    title: "Wie du mit der Plattform arbeitest",
    description:
      "Neue Fälle erfasst du separat, die tägliche Priorisierung erfolgt im Dashboard und vertiefte Analysen liegen bewusst in eigenen Ansichten.",
    helper: "Wenig Klicks, klare Rollen pro Bereich",
  },
  {
    eyebrow: "Übersicht",
    title: "Wofür die Bereiche gedacht sind",
    description:
      "Die Übersicht zeigt den aktuellen Zustand, die Warteschlange unterstützt die Bearbeitung und die Spezialansichten liefern KPI- und Abteilungsfokus.",
    helper: "Jeder Bereich hat einen klaren Zweck",
  },
  {
    eyebrow: "Nutzen",
    title: "Warum die Aufteilung sinnvoll ist",
    description:
      "Die Startseite erklärt, das Dashboard steuert die Arbeit und die Analyse-Seiten verhindern, dass alles auf einem einzigen Screen überladen wird.",
    helper: "Weniger Redundanz, mehr Orientierung",
  },
];

const WORKFLOW_STEPS = [
  {
    step: "1",
    title: "Start verstehen",
    description:
      "Auf dieser Seite erhältst du den Ablauf, die Rollen der einzelnen Bereiche und den besten Einstieg für den täglichen Betrieb.",
  },
  {
    step: "2",
    title: "Im Dashboard steuern",
    description:
      "Oben in der Übersicht findest du die Schnellzugriffe für Arbeitsbereiche, Erfassung, KPIs und Abteilungen.",
  },
  {
    step: "3",
    title: "Fallbezogen vertiefen",
    description:
      "Erst wenn nötig wechselst du in Ticketdetails, KPI-Auswertungen oder die Abteilungsübersicht für Entscheidungen und Reporting.",
  },
];

function LandingInfoCard({ eyebrow, title, description, helper }) {
  return (
    <div className="dashboard-module-card">
      <span className="dashboard-module-eyebrow">{eyebrow}</span>
      <h3>{title}</h3>
      <p>{description}</p>
      <div className="dashboard-module-footer dashboard-module-footer-static">
        <span>{helper}</span>
      </div>
    </div>
  );
}

function WorkflowCard({ step, title, description }) {
  return (
    <div className="dashboard-process-card">
      <span className="dashboard-process-step">{step}</span>
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  );
}

export default function DashboardLandingPage() {
  return (
    <div className="app-shell dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Ticket-Triage-Plattform</p>
          <h1>Ein klarer Start für Erklärung, Bedienung und Übersicht</h1>
          <p className="subtitle">
            Diese Startseite dient bewusst als Orientierung. Sie erklärt den Ablauf der Plattform, die Rolle der
            einzelnen Bereiche und wie du am schnellsten in die tägliche Arbeit einsteigst.
          </p>
          <div className="hero-guide">
            <p>
              Der eigentliche Arbeitsbereich ist die Dashboard-Übersicht. Dort liegen oben alle wichtigen
              Schnellzugriffe, während diese Seite den Einstieg erklärt und den Nutzen der Struktur sichtbar macht.
            </p>
            <ul>
              <li>Nutze die Startseite, um Bedienlogik und Aufbau zu verstehen.</li>
              <li>Wechsle danach in die Übersicht für Priorisierung, Warteschlange und operative Arbeit.</li>
              <li>Öffne KPI- und Abteilungsansichten nur dann, wenn du gezielt analysieren möchtest.</li>
            </ul>
          </div>
        </div>

        <div className="hero-summary-card">
          <span className="hero-summary-label">Einstieg</span>
          <strong className="hero-summary-value">3</strong>
          <span className="hero-summary-text">klare Schritte vom Verstehen bis zur Bearbeitung</span>
        </div>
      </section>

      <section className="dashboard-section-heading">
        <p className="eyebrow">Plattformüberblick</p>
        <h2>Wofür die einzelnen Bereiche gedacht sind</h2>
        <p>
          Die Startseite erklärt den Aufbau, während die Übersicht oben mit Schnellzugriffen als tägliche
          Steuerzentrale dient.
        </p>
      </section>

      <section className="dashboard-module-grid" aria-label="Plattformüberblick">
        {OVERVIEW_CARDS.map((card) => (
          <LandingInfoCard key={card.title} {...card} />
        ))}
      </section>

      <section className="dashboard-process-section" aria-label="Bedienablauf">
        <div className="dashboard-section-heading">
          <p className="eyebrow">Bedienung</p>
          <h2>So arbeitest du am einfachsten mit der Plattform</h2>
          <p>
            Die Oberfläche ist so aufgeteilt, dass Orientierung, tägliche Bearbeitung und vertiefte Analyse sauber
            getrennt bleiben.
          </p>
        </div>

        <div className="dashboard-process-grid">
          {WORKFLOW_STEPS.map((item) => (
            <WorkflowCard key={item.step} {...item} />
          ))}
        </div>
      </section>
    </div>
  );
}
