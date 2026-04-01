import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import SectionCard from "../components/SectionCard";
import TicketList from "../components/TicketList";
import Badge from "../components/Badge";
import { useToast } from "../components/ToastProvider";
import { DEPARTMENTS, normalizeDepartment } from "../../domain/constants/departments";
import { fetchTickets, triageTicket } from "../../infrastructure/http/api";
import { loadUserSettings } from "../../infrastructure/storage/userSettingsStore";

const WORKSPACE_TABS = [
  { id: "overview", label: "Übersicht" },
  { id: "tickets", label: "Ticket-Warteschlange" },
  { id: "operations", label: "Nächste Schritte" },
];

function StatCard({ label, value, accent, helper }) {
  return (
    <div className={`stat-card stat-card-${accent}`}>
      <div className="stat-card-top">
        <span className="stat-label">{label}</span>
        <span className="stat-dot" />
      </div>
      <strong className="stat-value">{value}</strong>
      <span className="stat-helper">{helper}</span>
    </div>
  );
}

function InsightCard({ label, value, description }) {
  return (
    <div className="insight-card">
      <span className="insight-label">{label}</span>
      <strong>{value}</strong>
      <p>{description}</p>
    </div>
  );
}

function TicketPreviewPanel({ title, actionLabel, onAction, tickets, emptyMessage }) {
  return (
    <SectionCard
      title={title}
      actions={
        onAction ? (
          <button type="button" className="secondary-button" onClick={onAction}>
            {actionLabel}
          </button>
        ) : null
      }
    >
      {tickets.length ? (
        <div className="dashboard-ticket-stack">
          {tickets.map((ticket) => (
            <Link key={getTicketId(ticket)} to={`/tickets/${getTicketId(ticket)}`} className="dashboard-ticket-row">
              <div className="dashboard-ticket-copy">
                <strong>{ticket.title}</strong>
                <p>{ticket.description || "Keine Beschreibung verfügbar."}</p>
                <span>{ticket.reporter || "Unbekannter Reporter"} · {normalizeDepartment(ticket.department)}</span>
              </div>
              <div className="dashboard-ticket-badges">
                <Badge value={getTicketPriority(ticket)} type="priority" />
                <Badge value={ticket.status} type="status" />
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <div className="list-empty-state">
          <strong>Keine Einträge</strong>
          <p>{emptyMessage}</p>
        </div>
      )}
    </SectionCard>
  );
}

function OperationalPanel({ title, subtitle, children }) {
  return (
    <div className="operational-panel">
      <div className="operational-panel-header">
        <span className="operational-panel-eyebrow">Operative Sicht</span>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="operational-panel-body">{children}</div>
    </div>
  );
}

function DashboardLoadingState() {
  return (
    <div className="dashboard-loading-state">
      <div className="loading-card shimmer" />
      <div className="loading-grid">
        <div className="loading-block shimmer" />
        <div className="loading-block shimmer" />
        <div className="loading-block shimmer" />
        <div className="loading-block shimmer" />
      </div>
    </div>
  );
}

function DashboardEmptyState({ onCreateSample, onGoToCreate, submittingTriage }) {
  return (
    <div className="dashboard-empty-state">
      <span className="empty-state-eyebrow">Leerer Arbeitsbereich</span>
      <h3>Noch keine Tickets vorhanden</h3>
      <p>
        Starte mit einem Beispiel oder springe direkt in die Erfassung. Danach füllen sich Übersicht,
        Abteilungen und KPI-Bereiche automatisch.
      </p>
      <div className="empty-state-actions">
        <button type="button" onClick={onCreateSample} disabled={submittingTriage}>
          {submittingTriage ? "Wird angelegt..." : "Beispielticket anlegen"}
        </button>
        <button type="button" className="secondary-button" onClick={onGoToCreate}>
          Zur Ticket-Erfassung
        </button>
      </div>
    </div>
  );
}

function DashboardCommandButton({ label, helper, onClick, active = false, emphasis = "neutral" }) {
  return (
    <button
      type="button"
      className={`dashboard-command-button dashboard-command-button-${emphasis} ${active ? "active" : ""}`}
      onClick={onClick}
    >
      <strong>{label}</strong>
      <span>{helper}</span>
    </button>
  );
}

function DistributionCard({ eyebrow, title, items, accent, emptyMessage, maxItems = 5 }) {
  const visibleItems = items.slice(0, maxItems);
  const total = items.reduce((sum, item) => sum + item.value, 0);
  const maxValue = visibleItems.reduce((currentMax, item) => Math.max(currentMax, item.value), 0);

  return (
    <div className="distribution-card">
      <div className="distribution-card-header">
        <span className="distribution-title">{eyebrow}</span>
        <h3>{title}</h3>
      </div>

      {visibleItems.length ? (
        <div className="distribution-list">
          {visibleItems.map((item) => {
            const share = total ? Math.round((item.value / total) * 100) : 0;
            const width = maxValue ? Math.max(Math.round((item.value / maxValue) * 100), item.value > 0 ? 10 : 0) : 0;

            return (
              <div key={item.name} className="distribution-row">
                <div className="distribution-row-top">
                  <span className="distribution-label">{item.name}</span>
                  <span className="distribution-meta">
                    {item.value} Tickets · {share}%
                  </span>
                </div>
                <div className="distribution-bar-track">
                  <div className={`distribution-bar distribution-bar-${accent}`} style={{ width: `${width}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="distribution-empty">{emptyMessage}</p>
      )}
    </div>
  );
}

function normalizeLabel(value) {
  return String(value || "unknown").toLowerCase();
}

function buildDistributionFromAccessor(tickets, accessor, orderedLabels = [], includeEmptyLabels = false) {
  const counts = new Map();

  tickets.forEach((ticket) => {
    const normalized = normalizeLabel(accessor(ticket));
    counts.set(normalized, (counts.get(normalized) || 0) + 1);
  });

  const orderedItems = [];
  const total = tickets.length || 1;

  orderedLabels.forEach((label) => {
    const key = normalizeLabel(label);
    const value = counts.get(key) || 0;
    if (value > 0 || includeEmptyLabels) {
      orderedItems.push({
        name: label,
        value,
        percent: Math.round((value / total) * 100),
      });
    }
    counts.delete(key);
  });

  Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .forEach(([name, value]) => {
      orderedItems.push({
        name,
        value,
        percent: Math.round((value / total) * 100),
      });
    });

  return orderedItems;
}

function getTicketPriority(ticket) {
  return ticket.decision?.final_priority || ticket.priority || ticket.analysis?.predicted_priority || "unknown";
}

function getTicketCategory(ticket) {
  return ticket.decision?.final_category || ticket.category || ticket.analysis?.predicted_category || "unknown";
}

function getTicketId(ticket) {
  return ticket.ticket_id || ticket.id;
}

function getPriorityScore(priority) {
  return {
    critical: 4,
    high: 3,
    medium: 2,
    low: 1,
    unknown: 0,
  }[normalizeLabel(priority)] || 0;
}

function isOpenTicket(ticket) {
  return ["new", "triaged", "reviewed"].includes(normalizeLabel(ticket.status));
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();

  const [tickets, setTickets] = useState([]);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [submittingTriage, setSubmittingTriage] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [activeWorkspace, setActiveWorkspace] = useState("overview");

  async function loadTickets({ silent = false } = {}) {
    try {
      if (!silent) {
        setLoadingTickets(true);
      }

      const data = await fetchTickets();
      setTickets(data);
    } catch (err) {
      showToast({
        type: "error",
        title: "Laden fehlgeschlagen",
        message: err?.response?.data?.detail || "Die Tickets konnten nicht geladen werden.",
      });
    } finally {
      if (!silent) {
        setLoadingTickets(false);
      }
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  useEffect(() => {
    const querySearch = searchParams.get("q") || "";
    const queryWorkspace = searchParams.get("workspace");
    const defaultWorkspace = loadUserSettings().dashboardWorkspace;

    setSearch(querySearch);

    if (WORKSPACE_TABS.some((tab) => tab.id === queryWorkspace)) {
      setActiveWorkspace(queryWorkspace);
    } else if (WORKSPACE_TABS.some((tab) => tab.id === defaultWorkspace)) {
      setActiveWorkspace(defaultWorkspace);
    } else {
      setActiveWorkspace("overview");
    }
  }, [searchParams]);

  const updateUrlState = ({ nextWorkspace = activeWorkspace, nextSearch = search } = {}) => {
    const nextParams = new URLSearchParams(searchParams);

    if (nextWorkspace) {
      nextParams.set("workspace", nextWorkspace);
    } else {
      nextParams.delete("workspace");
    }

    if (nextSearch && nextSearch.trim()) {
      nextParams.set("q", nextSearch.trim());
    } else {
      nextParams.delete("q");
    }

    setSearchParams(nextParams, { replace: true });
  };

  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      const normalizedSearch = search.toLowerCase();

      const matchesSearch =
        (ticket.title || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.description || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.reporter || "").toLowerCase().includes(normalizedSearch) ||
        String(getTicketId(ticket)).toLowerCase().includes(normalizedSearch);

      const matchesStatus = statusFilter === "all" ? true : ticket.status === statusFilter;
      const matchesDepartment =
        departmentFilter === "all" ? true : normalizeDepartment(ticket.department) === departmentFilter;

      return matchesSearch && matchesStatus && matchesDepartment;
    });
  }, [tickets, search, statusFilter, departmentFilter]);

  const totalTickets = tickets.length;
  const triagedCount = tickets.filter((ticket) => ticket.status === "triaged").length;
  const reviewedCount = tickets.filter((ticket) => ticket.status === "reviewed" || ticket.decision).length;
  const assignedCount = tickets.filter((ticket) => ticket.status === "assigned" || ticket.assignment).length;
  const openTicketsCount = tickets.filter((ticket) => isOpenTicket(ticket)).length;
  const newTicketsCount = tickets.filter((ticket) => ticket.status === "new").length;

  const reviewedTickets = tickets.filter((ticket) => ticket.decision);
  const acceptedAiCount = reviewedTickets.filter((ticket) => ticket.decision?.accepted_ai_suggestion === true).length;
  const acceptanceRate = reviewedTickets.length ? Math.round((acceptedAiCount / reviewedTickets.length) * 100) : 0;
  const reviewCoverage = totalTickets ? Math.round((reviewedCount / totalTickets) * 100) : 0;
  const assignmentRate = totalTickets ? Math.round((assignedCount / totalTickets) * 100) : 0;

  const statusDistribution = buildDistributionFromAccessor(
    tickets,
    (ticket) => ticket.status,
    ["new", "triaged", "reviewed", "assigned"]
  );

  const priorityDistribution = buildDistributionFromAccessor(
    tickets,
    (ticket) => getTicketPriority(ticket),
    ["low", "medium", "high", "critical"]
  );

  const departmentDistribution = buildDistributionFromAccessor(
    tickets,
    (ticket) => normalizeDepartment(ticket.department),
    DEPARTMENTS,
    true
  );

  const activeDepartments = departmentDistribution.filter((item) => item.value > 0);
  const highlightedDepartments = activeDepartments.slice(0, 5);

  const criticalTickets = useMemo(
    () =>
      [...tickets]
        .filter((ticket) => ["high", "critical"].includes(normalizeLabel(getTicketPriority(ticket))))
        .sort((left, right) => getPriorityScore(getTicketPriority(right)) - getPriorityScore(getTicketPriority(left)))
        .slice(0, 5),
    [tickets]
  );

  const reviewQueueTickets = useMemo(
    () => tickets.filter((ticket) => ticket.status === "triaged").slice(0, 5),
    [tickets]
  );

  const recentTickets = useMemo(
    () => [...tickets].reverse().slice(0, 5),
    [tickets]
  );

  const needsAttentionTickets = useMemo(
    () =>
      [...tickets]
        .filter((ticket) => ["high", "critical"].includes(normalizeLabel(getTicketPriority(ticket))) || ticket.status === "triaged")
        .sort((left, right) => getPriorityScore(getTicketPriority(right)) - getPriorityScore(getTicketPriority(left)))
        .slice(0, 5),
    [tickets]
  );

  async function handleCreateSampleTicket() {
    try {
      setSubmittingTriage(true);

      const result = await triageTicket({
        title: "Beispiel: Login-Störung in Produktion",
        description: "Benutzerinnen und Benutzer können sich seit dem letzten Deployment teilweise nicht mehr anmelden.",
        reporter: "System Demo",
        source: "internal",
      });

      await loadTickets({ silent: true });

      showToast({
        type: "success",
        title: "Beispielticket erstellt",
        message: "Ein Beispielticket wurde erstellt und dem Dashboard hinzugefügt.",
      });

      navigate(`/tickets/${result.ticket_id}`);
    } catch (err) {
      showToast({
        type: "error",
        title: "Erstellung fehlgeschlagen",
        message: err?.response?.data?.detail || "Das Beispielticket konnte nicht erstellt werden.",
      });
    } finally {
      setSubmittingTriage(false);
    }
  }

  const handleWorkspaceChange = (workspace) => {
    setActiveWorkspace(workspace);
    updateUrlState({ nextWorkspace: workspace });
  };

  const handleSearchChange = (value) => {
    setSearch(value);
    updateUrlState({ nextWorkspace: "tickets", nextSearch: value });
  };

  if (loadingTickets && tickets.length === 0) {
    return (
      <div className="app-shell dashboard-shell">
        <DashboardLoadingState />
      </div>
    );
  }

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Operative Steuerung</p>
          <h1>Fokussierte Arbeitsübersicht für Triage und Routing</h1>
          <p className="subtitle">
            Diese Ansicht bündelt die wichtigsten Kennzahlen, den direkten Zugang zur Warteschlange und die
            dringendsten Vorgänge für den laufenden Betrieb.
          </p>
          <div className="hero-guide">
            <p>
              Nutze oben die Schnellzugriffe, springe in die Warteschlange für Such- und Filterarbeit und arbeite
              kritische Fälle direkt aus den Fokuslisten heraus ab.
            </p>
          </div>
        </div>

        <div className="hero-summary-card">
          <span className="hero-summary-label">Kritische Fälle</span>
          <strong className="hero-summary-value">{criticalTickets.length}</strong>
          <span className="hero-summary-text">Tickets mit hoher oder kritischer Priorität im aktuellen Bestand</span>
          <div className="hero-summary-metrics" aria-label="Operative Schnellkennzahlen">
            <div className="hero-summary-metric">
              <span>Offen</span>
              <strong>{openTicketsCount}</strong>
            </div>
            <div className="hero-summary-metric">
              <span>Review</span>
              <strong>{reviewCoverage}%</strong>
            </div>
            <div className="hero-summary-metric">
              <span>Zuweisung</span>
              <strong>{assignmentRate}%</strong>
            </div>
          </div>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Arbeitszentrale</span>
          <span>•</span>
          <span>{WORKSPACE_TABS.find((tab) => tab.id === activeWorkspace)?.label || "Übersicht"}</span>
        </div>
        <p className="dashboard-context-copy">
          Die Übersicht priorisiert Entscheidungen, die Warteschlange unterstützt die Bearbeitung und die operative
          Sicht bündelt Dringlichkeit und letzte Aktivitäten.
        </p>
      </section>

      <section className="dashboard-command-bar" aria-label="Schnellzugriffe">
        <div className="dashboard-command-section">
          <div className="dashboard-command-heading">
            <span>Arbeitsbereiche</span>
            <p>Wechsle zwischen Überblick, Warteschlange und Handlungsbedarf.</p>
          </div>
          <div className="dashboard-command-grid">
            <DashboardCommandButton
              label="Übersicht"
              helper="Kernzahlen und Fokuslisten"
              active={activeWorkspace === "overview"}
              emphasis="primary"
              onClick={() => handleWorkspaceChange("overview")}
            />
            <DashboardCommandButton
              label="Warteschlange"
              helper="Suchen, filtern und Tickets öffnen"
              active={activeWorkspace === "tickets"}
              emphasis="primary"
              onClick={() => handleWorkspaceChange("tickets")}
            />
            <DashboardCommandButton
              label="Nächste Schritte"
              helper="Dringende Fälle zuerst bearbeiten"
              active={activeWorkspace === "operations"}
              emphasis="primary"
              onClick={() => handleWorkspaceChange("operations")}
            />
          </div>
        </div>

        <div className="dashboard-command-section">
          <div className="dashboard-command-heading">
            <span>Direktaktionen</span>
            <p>Springe in Erfassung oder Analysebereiche, ohne den Fokus zu verlieren.</p>
          </div>
          <div className="dashboard-command-grid dashboard-command-grid-actions">
            <DashboardCommandButton
              label="Ticket erfassen"
              helper="Neuen Fall anlegen"
              emphasis="secondary"
              onClick={() => navigate("/dashboard/create")}
            />
            <DashboardCommandButton
              label="KPIs"
              helper="Status, Trends und Volumen"
              emphasis="secondary"
              onClick={() => navigate("/reports/kpis")}
            />
            <DashboardCommandButton
              label="Abteilungen"
              helper="Ownership und Verteilung"
              emphasis="secondary"
              onClick={() => navigate("/reports/departments")}
            />
            <DashboardCommandButton
              label="Reports"
              helper="Trend- und Backlog-Sicht"
              emphasis="secondary"
              onClick={() => navigate("/reports")}
            />
          </div>
        </div>
      </section>

      {tickets.length === 0 ? (
        <DashboardEmptyState
          onCreateSample={handleCreateSampleTicket}
          onGoToCreate={() => navigate("/dashboard/create")}
          submittingTriage={submittingTriage}
        />
      ) : (
        <>
          <section className="stats-grid" aria-label="Dashboard-KPIs">
            <StatCard label="Gesamt" value={totalTickets} helper="Alle Tickets im aktuellen Bestand" accent="neutral" />
            <StatCard label="Offen" value={openTicketsCount} helper="Noch nicht final weitergeleitete Fälle" accent="info" />
            <StatCard label="Kritisch" value={criticalTickets.length} helper="Hohe oder kritische Prioritäten" accent="danger" />
            <StatCard label="Triagiert" value={triagedCount} helper="Für die manuelle Prüfung vorbereitet" accent="info" />
            <StatCard label="Geprüft" value={reviewedCount} helper="Bereits manuell validiert" accent="warning" />
            <StatCard label="Aktive Abteilungen" value={activeDepartments.length} helper="Bereiche mit mindestens einem Ticket" accent="success" />
          </section>

          <section className="workspace-shell">
            <div className="workspace-header">
              <div>
                <p className="workspace-eyebrow">Arbeitsbereiche</p>
                <h2>
                  {activeWorkspace === "overview"
                    ? "Operativer Überblick"
                    : activeWorkspace === "tickets"
                      ? "Ticket-Warteschlange"
                      : "Handlungsbedarf und letzte Bewegungen"}
                </h2>
                <p>
                  {activeWorkspace === "overview"
                    ? "Fokuslisten, Kennzahlen und Verteilungen für schnelle Lagebeurteilung."
                    : activeWorkspace === "tickets"
                      ? "Suche, filtere und springe direkt in den passenden Vorgang."
                      : "Konzentriere dich auf kritische Tickets und aktuelle Aktivitäten im Betrieb."}
                </p>
              </div>
              <div className="workspace-header-note">
                <strong>Aktiver Bereich</strong>
                <span>{WORKSPACE_TABS.find((tab) => tab.id === activeWorkspace)?.label || "Übersicht"}</span>
              </div>
            </div>

            {activeWorkspace === "overview" ? (
              <>
                <section className="insight-strip">
                  <InsightCard
                    label="Prüfqueue"
                    value={`${reviewQueueTickets.length} Tickets`}
                    description="So viele Fälle warten aktuell auf einen manuellen Entscheid."
                  />
                  <InsightCard
                    label="Prüfabdeckung"
                    value={`${reviewCoverage}%`}
                    description="Anteil der Tickets, die bereits geprüft oder zugewiesen wurden."
                  />
                  <InsightCard
                    label="KI-Akzeptanz"
                    value={`${acceptanceRate}%`}
                    description="Bestätigte KI-Empfehlungen bezogen auf alle bisherigen Prüfungen."
                  />
                  <InsightCard
                    label="Neue Tickets"
                    value={`${newTicketsCount}`}
                    description="Frisch eingegangene Fälle, die im aktuellen Bestand noch offen sind."
                  />
                </section>

                <section className="dashboard-overview-grid" aria-label="Fokuslisten">
                  <TicketPreviewPanel
                    title="Kritische Tickets"
                    actionLabel="Zur Warteschlange"
                    onAction={() => handleWorkspaceChange("tickets")}
                    tickets={criticalTickets}
                    emptyMessage="Aktuell sind keine kritischen Tickets vorhanden."
                  />
                  <TicketPreviewPanel
                    title="Prüfqueue"
                    actionLabel="Prüfbereich öffnen"
                    onAction={() => handleWorkspaceChange("operations")}
                    tickets={reviewQueueTickets}
                    emptyMessage="Es warten derzeit keine Tickets auf eine Prüfung."
                  />
                  <TicketPreviewPanel
                    title="Neueste Tickets"
                    actionLabel="Alle ansehen"
                    onAction={() => handleWorkspaceChange("tickets")}
                    tickets={recentTickets}
                    emptyMessage="Noch keine Ticketaktivität verfügbar."
                  />
                </section>

                <section className="analytics-grid" aria-label="Verdichtete Verteilungen">
                  <DistributionCard
                    eyebrow="Ablauf"
                    title="Statusverteilung"
                    items={statusDistribution.filter((item) => item.value > 0)}
                    accent="info"
                    emptyMessage="Noch keine Statusdaten verfügbar."
                  />
                  <DistributionCard
                    eyebrow="Risiko"
                    title="Prioritäten"
                    items={priorityDistribution.filter((item) => item.value > 0)}
                    accent="warning"
                    emptyMessage="Noch keine Prioritätsdaten verfügbar."
                  />
                  <DistributionCard
                    eyebrow="Verantwortung"
                    title="Aktive Abteilungen"
                    items={highlightedDepartments}
                    accent="success"
                    emptyMessage="Noch keine Abteilungen mit Tickets vorhanden."
                  />
                </section>

                <section className="management-grid" aria-label="Management Summary">
                  <div className="management-card management-card-info">
                    <span className="management-label">Offene Tickets</span>
                    <strong className="management-value">{openTicketsCount}</strong>
                    <span className="management-helper">Fälle ohne abgeschlossene Weitergabe</span>
                  </div>
                  <div className="management-card management-card-warning">
                    <span className="management-label">Review-Abdeckung</span>
                    <strong className="management-value">{reviewCoverage}%</strong>
                    <span className="management-helper">Prüf- und Zuweisungsquote im Bestand</span>
                  </div>
                  <div className="management-card management-card-success">
                    <span className="management-label">Zuweisungsquote</span>
                    <strong className="management-value">{assignmentRate}%</strong>
                    <span className="management-helper">Tickets mit dokumentierter Teamzuweisung</span>
                  </div>
                </section>
              </>
            ) : null}

            {activeWorkspace === "tickets" ? (
              <section className="workspace-grid" aria-label="Bereich Ticket-Warteschlange">
                <SectionCard title="Filter & Suche">
                  <div className="filter-stack">
                    <label>
                      Suchbegriff
                      <input
                        className="toolbar-input"
                        placeholder="Titel, Beschreibung, ID oder Reporter durchsuchen"
                        value={search}
                        onChange={(event) => handleSearchChange(event.target.value)}
                      />
                    </label>
                    <label>
                      Status
                      <select
                        className="toolbar-select"
                        value={statusFilter}
                        onChange={(event) => setStatusFilter(event.target.value)}
                      >
                        <option value="all">Alle Status</option>
                        <option value="new">Neu</option>
                        <option value="triaged">Triagiert</option>
                        <option value="reviewed">Geprüft</option>
                        <option value="assigned">Zugewiesen</option>
                      </select>
                    </label>
                    <label>
                      Abteilung
                      <select
                        className="toolbar-select"
                        value={departmentFilter}
                        onChange={(event) => setDepartmentFilter(event.target.value)}
                      >
                        <option value="all">Alle Abteilungen</option>
                        {DEPARTMENTS.map((department) => (
                          <option key={department} value={department}>
                            {department}
                          </option>
                        ))}
                      </select>
                    </label>
                    <p className="filter-hint">
                      Die Warteschlange ist jetzt dein operativer Suchraum. Für neue Fälle oder verdichtete Analysen
                      wechselst du direkt über die Schnellzugriffe.
                    </p>
                  </div>
                </SectionCard>

                <SectionCard
                  title={`Ticket-Warteschlange (${filteredTickets.length})`}
                  actions={(
                    <button type="button" className="secondary-button" onClick={() => navigate("/dashboard/create")}>
                      Neues Ticket
                    </button>
                  )}
                >
                  {loadingTickets && tickets.length > 0 ? (
                    <div className="inline-loading-state shimmer">Ticketdaten werden aktualisiert…</div>
                  ) : null}

                  {!loadingTickets && filteredTickets.length === 0 ? (
                    <div className="list-empty-state">
                      <strong>Keine Tickets passend zu den aktuellen Filtern</strong>
                      <p>Reduziere die Filter oder springe in die Übersicht zurück.</p>
                    </div>
                  ) : (
                    <TicketList tickets={filteredTickets} loading={loadingTickets && tickets.length === 0} selectedTicketId={null} />
                  )}
                </SectionCard>
              </section>
            ) : null}

            {activeWorkspace === "operations" ? (
              <section className="operations-grid" aria-label="Operational Panels">
                <OperationalPanel
                  title="Handlungsbedarf"
                  subtitle="Tickets mit hoher Priorität oder noch offenem Prüfbedarf."
                >
                  {needsAttentionTickets.length ? (
                    <div className="ops-list">
                      {needsAttentionTickets.map((ticket) => (
                        <button
                          key={getTicketId(ticket)}
                          type="button"
                          className="ops-list-item"
                          onClick={() => navigate(`/tickets/${getTicketId(ticket)}`)}
                        >
                          <div className="ops-list-top">
                            <strong>{ticket.title}</strong>
                            <Badge value={getTicketPriority(ticket)} type="priority" />
                          </div>
                          <div className="ops-list-meta">
                            <Badge value={ticket.status} type="status" />
                            <Badge value={getTicketCategory(ticket)} type="category" />
                          </div>
                          <p>{ticket.description || "Keine Beschreibung verfügbar."}</p>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="ops-empty">Aktuell sind keine dringenden Tickets markiert.</p>
                  )}
                </OperationalPanel>

                <OperationalPanel
                  title="Letzte Aktivitäten"
                  subtitle="Zuletzt erfasste Tickets für schnelles Nachfassen."
                >
                  {recentTickets.length ? (
                    <div className="ops-list">
                      {recentTickets.map((ticket) => (
                        <button
                          key={getTicketId(ticket)}
                          type="button"
                          className="ops-list-item"
                          onClick={() => navigate(`/tickets/${getTicketId(ticket)}`)}
                        >
                          <div className="ops-list-top">
                            <strong>{ticket.title}</strong>
                            <Badge value={ticket.status} type="status" />
                          </div>
                          <div className="ops-list-meta">
                            <span>Reporter: {ticket.reporter || "—"}</span>
                            <span>Abteilung: {normalizeDepartment(ticket.department) || "—"}</span>
                          </div>
                          <p>{ticket.description || "Keine Beschreibung verfügbar."}</p>
                        </button>
                      ))}
                    </div>
                  ) : (
                    <p className="ops-empty">Noch keine Aktivitäten verfügbar.</p>
                  )}
                </OperationalPanel>
              </section>
            ) : null}
          </section>
        </>
      )}
    </div>
  );
}
