function formatMinutes(value) {
  if (value === null || value === undefined) return "—";
  const minutes = Math.max(0, Number(value));
  if (Number.isNaN(minutes)) return "—";
  if (minutes < 60) return `${minutes} min`;
  const h = Math.floor(minutes / 60);
  const rest = minutes % 60;
  return `${h}h${rest ? ` ${rest}m` : ""}`;
}

function solvabilityLabel(value) {
  switch ((value || "").toLowerCase()) {
    case "self-service":
      return "Self-Service";
    case "l1":
      return "L1";
    case "l2":
      return "L2";
    case "specialist":
      return "Spezialist";
    default:
      return value || "—";
  }
}

function compositeTone(score) {
  if (score >= 20) return "prio-critical";
  if (score >= 12) return "prio-high";
  if (score >= 6) return "prio-medium";
  return "prio-low";
}

export default function PrioritizationPanel({ prioritization, variant = "modal" }) {
  if (!prioritization) return null;

  const {
    impact_score: impact,
    urgency_score: urgency,
    effort_estimate_minutes: effort,
    solvability,
    composite_priority: composite,
    auto_resolve_eligible: autoResolve,
    runbook_url: runbookUrl,
    rationale,
    matched_rules: matchedRules,
  } = prioritization;

  const compositeRounded = Math.round(Number(composite ?? impact * urgency));
  const tone = compositeTone(compositeRounded);
  const solvabilityClass = `solvability-${String(solvability || "").toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;

  return (
    <div className={`prioritization-panel prioritization-panel-${variant}`}>
      <p className="eyebrow">Priorisierung & Aufwand</p>

      <div className="prioritization-grid">
        <div className="prioritization-card">
          <span className="prioritization-label" title="Wie wichtig ist dieser Vorgang fachlich/geschäftlich?">
            Wichtigkeit
          </span>
          <strong className="prioritization-value">{impact}/5</strong>
        </div>
        <div className="prioritization-card">
          <span className="prioritization-label" title="Wie schnell muss reagiert werden?">
            Dringlichkeit
          </span>
          <strong className="prioritization-value">{urgency}/5</strong>
        </div>
        <div className="prioritization-card">
          <span className="prioritization-label" title="Geschätzter Bearbeitungsaufwand">
            Aufwand
          </span>
          <strong className="prioritization-value">{formatMinutes(effort)}</strong>
        </div>
        <div className="prioritization-card">
          <span
            className="prioritization-label"
            title="Self-Service = vom Reporter selbst lösbar · L1/L2 = Service-Desk-Stufen · Spezialist = Fachexperte nötig"
          >
            Lösbarkeit
          </span>
          <span className={`pill ${solvabilityClass}`}>{solvabilityLabel(solvability)}</span>
        </div>
        <div className="prioritization-card prioritization-card-composite">
          <span
            className="prioritization-label"
            title="Prio-Score = Wichtigkeit × Dringlichkeit (1–25, sortiert den Backlog)"
          >
            Prio-Score
          </span>
          <span className={`prio-dot ${tone}`}>
            <span className="tabular-nums">{compositeRounded}</span>
          </span>
        </div>
      </div>

      {autoResolve && runbookUrl ? (
        <div className="prioritization-auto-resolve">
          <strong>⚡ Auto-Resolve-fähig.</strong>{" "}
          Self-Service-Lösung verfügbar — Reporter direkt auf Runbook leiten:{" "}
          <a href={runbookUrl} target="_blank" rel="noopener noreferrer">
            Runbook öffnen
          </a>
          .
        </div>
      ) : runbookUrl ? (
        <div className="prioritization-runbook">
          Standard-Runbook für diesen Fall:{" "}
          <a href={runbookUrl} target="_blank" rel="noopener noreferrer">
            {runbookUrl.replace(/^https?:\/\//, "")}
          </a>
        </div>
      ) : null}

      {rationale ? <p className="prioritization-rationale">{rationale}</p> : null}

      {matchedRules && matchedRules.length ? (
        <p className="prioritization-rules">
          Angewendete Regeln:{" "}
          {matchedRules.map((rule, idx) => (
            <code key={rule}>
              {rule}
              {idx < matchedRules.length - 1 ? ", " : ""}
            </code>
          ))}
        </p>
      ) : null}
    </div>
  );
}
