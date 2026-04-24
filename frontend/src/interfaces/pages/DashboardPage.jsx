import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useSetPageHeading } from "../components/PageHeadingContext";
import { useToast } from "../components/ToastProvider";
import { fetchTickets } from "../../infrastructure/http/api";

const OPEN_STATUSES = new Set(["new", "triaged", "in_review", "in_progress", "open", "assigned"]);

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function formatRelative(timestamp) {
  if (!timestamp) return "—";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "—";
  const diff = Math.max(0, Date.now() - date.getTime());
  const min = Math.floor(diff / 60_000);
  if (min < 1) return "jetzt";
  if (min < 60) return `vor ${min} Min`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `vor ${hr} Std`;
  const d = Math.floor(hr / 24);
  if (d < 7) return `vor ${d} Tg`;
  const w = Math.floor(d / 7);
  if (w < 5) return `vor ${w} Wo`;
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "2-digit" });
}

function initials(name) {
  if (!name) return "—";
  const parts = String(name).trim().split(/\s+/);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function priorityClass(priority) {
  const p = normalize(priority);
  if (p === "critical") return "prio-critical";
  if (p === "high") return "prio-high";
  if (p === "medium") return "prio-medium";
  return "prio-low";
}

function KpiTile({ label, value }) {
  return (
    <div className="kpi-tile">
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value tabular-nums">{value}</strong>
      <span className="kpi-delta kpi-delta-neutral">—</span>
    </div>
  );
}

function CategoryPill({ value }) {
  const v = normalize(value);
  const known = ["bug", "feature", "support", "requirement", "question"];
  const key = known.includes(v) ? v : "unknown";
  return <span className={`pill pill-cat-${key}`}>{value || "—"}</span>;
}

function FocusList({ title, items, emptyLabel }) {
  return (
    <section className="focus-panel">
      <header className="focus-panel-header">
        <h2>{title}</h2>
        <span className="focus-panel-count tabular-nums">{items.length}</span>
      </header>
      <ul className="focus-list">
        {items.length === 0 ? (
          <li className="focus-list-empty">{emptyLabel}</li>
        ) : (
          items.slice(0, 8).map((ticket) => (
            <li key={ticket.id} className="focus-row">
              <Link to={`/tickets/${ticket.id}`} className="focus-row-link">
                <span
                  className={`focus-row-dot prio-dot ${priorityClass(ticket.priority)}`}
                  aria-hidden="true"
                />
                <span className="focus-row-title">{ticket.title}</span>
                <span className="focus-row-avatar" title={ticket.assignee || ticket.reporter || ""}>
                  {initials(ticket.assignee || ticket.reporter)}
                </span>
                <span className="focus-row-time tabular-nums">
                  {formatRelative(ticket.created_at || ticket.updated_at)}
                </span>
              </Link>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}

/**
 * Verdichtete, aber informationsreichere Zeilen für die Kritisch-Spalte:
 * der Operator soll nicht nur den Titel sehen (der kann kryptisch sein wie
 * "WB-VIEWS-CLAUDIO Kritisch"), sondern auf einen Blick auch Kategorie,
 * Team/Abteilung und Reporter — damit er das Ticket einordnen kann
 * ohne es zu öffnen.
 */
function CriticalList({ title, items, emptyLabel }) {
  return (
    <section className="focus-panel focus-panel-emphasis">
      <header className="focus-panel-header">
        <h2>{title}</h2>
        <span className="focus-panel-count tabular-nums">{items.length}</span>
      </header>
      <ul className="focus-list">
        {items.length === 0 ? (
          <li className="focus-list-empty">{emptyLabel}</li>
        ) : (
          items.slice(0, 8).map((ticket) => {
            const scope = ticket.team || ticket.department || "—";
            return (
              <li key={ticket.id} className="critical-row">
                <Link to={`/tickets/${ticket.id}`} className="critical-row-link">
                  <span
                    className={`focus-row-dot prio-dot ${priorityClass(ticket.priority)}`}
                    aria-hidden="true"
                  />
                  <div className="critical-row-body">
                    <span className="critical-row-title">{ticket.title}</span>
                    <span className="critical-row-meta">
                      <CategoryPill value={ticket.category} />
                      <span className="critical-row-scope">{scope}</span>
                      <span className="critical-row-reporter">· {ticket.reporter || "—"}</span>
                    </span>
                  </div>
                  <span className="critical-row-time tabular-nums">
                    {formatRelative(ticket.created_at || ticket.updated_at)}
                  </span>
                </Link>
              </li>
            );
          })
        )}
      </ul>
    </section>
  );
}

export default function DashboardPage() {
  const { showToast } = useToast();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- external-fetch sync; setting the loading flag is exactly what effects are for.
    setLoading(true);
    fetchTickets()
      .then((data) => {
        if (!cancelled) setTickets(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        if (!cancelled) {
          showToast({
            type: "error",
            title: "Tickets konnten nicht geladen werden",
            message: "Aktualisiere die Seite oder prüfe die Backend-Verbindung.",
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [showToast]);

  useSetPageHeading("Übersicht", tickets.length || null);

  const kpis = useMemo(() => {
    const total = tickets.length;
    const open = tickets.filter((t) => OPEN_STATUSES.has(normalize(t.status))).length;
    const critical = tickets.filter((t) => normalize(t.priority) === "critical").length;
    const triaged = tickets.filter((t) => normalize(t.status) === "triaged" || t.analysis).length;
    const reviewed = tickets.filter((t) => t.decision).length;
    const departments = new Set(
      tickets.map((t) => normalize(t.department)).filter(Boolean),
    ).size;
    return { total, open, critical, triaged, reviewed, departments };
  }, [tickets]);

  const focusLists = useMemo(() => {
    const sortedByCreated = [...tickets].sort((a, b) => {
      const da = new Date(a.created_at || 0).getTime();
      const db = new Date(b.created_at || 0).getTime();
      return db - da;
    });
    const critical = sortedByCreated.filter(
      (t) => normalize(t.priority) === "critical" && normalize(t.status) !== "closed",
    );
    const reviewQueue = sortedByCreated.filter((t) => t.analysis && !t.decision);
    const recent = sortedByCreated;
    return { critical, reviewQueue, recent };
  }, [tickets]);

  return (
    <div className="app-shell overview-shell">
      <div className="overview-kpi-row">
        <KpiTile label="Gesamt" value={kpis.total} />
        <KpiTile label="Offen" value={kpis.open} />
        <KpiTile label="Kritisch" value={kpis.critical} />
        <KpiTile label="Triagiert" value={kpis.triaged} />
        <KpiTile label="Geprüft" value={kpis.reviewed} />
        <KpiTile label="Aktive Abteilungen" value={kpis.departments} />
      </div>

      <div className="overview-focus-row">
        <CriticalList
          title="Kritische Tickets"
          items={focusLists.critical}
          emptyLabel={loading ? "Wird geladen …" : "Keine kritischen Tickets."}
        />
        <FocusList
          title="Prüfqueue"
          items={focusLists.reviewQueue}
          emptyLabel={loading ? "Wird geladen …" : "Keine Tickets warten auf Review."}
        />
        <FocusList
          title="Neueste Tickets"
          items={focusLists.recent}
          emptyLabel={loading ? "Wird geladen …" : "Keine Tickets vorhanden."}
        />
      </div>
    </div>
  );
}
