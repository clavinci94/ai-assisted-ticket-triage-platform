import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import SectionCard from "../components/SectionCard";
import TicketList from "../components/TicketList";
import Badge from "../components/Badge";
import { useToast } from "../components/ToastProvider";
import { fetchDashboardAnalytics, fetchTickets, triageTicket } from "../lib/api";
import { DEPARTMENTS, normalizeDepartment } from "../lib/departments";

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
  return ticket.final_priority || ticket.priority || ticket.analysis?.predicted_priority || "unknown";
}

function getTicketCategory(ticket) {
  return ticket.final_category || ticket.category || ticket.analysis?.predicted_category || "unknown";
}

function getTicketId(ticket) {
  return ticket.ticket_id || ticket.id;
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [tickets, setTickets] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loadingTickets, setLoadingTickets] = useState(false);
  const [submittingTriage, setSubmittingTriage] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [departmentFilter, setDepartmentFilter] = useState("all");
  const [activeWorkspace, setActiveWorkspace] = useState("overview");

  async function loadAnalytics() {
    try {
      const data = await fetchDashboardAnalytics();
      setAnalytics(data);
    } catch (err) {
      showToast({
        type: "error",
        title: "Analysen konnten nicht geladen werden",
        message: err?.response?.data?.detail || "Die Dashboard-Analysen konnten nicht geladen werden.",
      });
    }
  }

  async function loadTickets({ silent = false } = {}) {
    try {
      if (!silent) {
        setLoadingTickets(true);
      }

      const data = await fetchTickets();
      setTickets(data);
      await loadAnalytics();
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

  const dashboardStats = analytics?.stats || {
    total: tickets.length,
    triaged: tickets.filter((ticket) => ticket.status === "triaged").length,
    reviewed: tickets.filter((ticket) => ticket.status === "reviewed").length,
    assigned: tickets.filter((ticket) => ticket.status === "assigned").length,
  };

  const statusDistribution =
    analytics?.status_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => ticket.status, ["new", "triaged", "reviewed", "assigned"]);

  const priorityDistribution =
    analytics?.priority_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => getTicketPriority(ticket), ["low", "medium", "high", "critical"]);

  const departmentDistribution =
    analytics?.department_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => normalizeDepartment(ticket.department), DEPARTMENTS, true);

  const managementMetrics = analytics?.management_metrics || {
    reviewed_count: dashboardStats.reviewed,
    accepted_ai_count: 0,
    acceptance_rate: 0,
    assignment_rate: 0,
    review_coverage: 0,
  };

  const needsAttentionTickets = analytics?.needs_attention || [];
  const recentTickets = analytics?.recent_activity || [...tickets].reverse().slice(0, 5);

  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      const normalizedSearch = search.toLowerCase();

      const matchesSearch =
        (ticket.title || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.description || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.reporter || "").toLowerCase().includes(normalizedSearch);

      const matchesStatus = statusFilter === "all" ? true : ticket.status === statusFilter;
      const matchesDepartment =
        departmentFilter === "all" ? true : normalizeDepartment(ticket.department) === departmentFilter;

      return matchesSearch && matchesStatus && matchesDepartment;
    });
  }, [tickets, search, statusFilter, departmentFilter]);

  const activeDepartments = departmentDistribution.filter((item) => item.value > 0);
  const highlightedDepartments = activeDepartments.slice(0, 5);

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
          <p className="eyebrow">Ticket-Triage-Plattform</p>
          <h1>Ein Dashboard, klare Wege, keine Doppelungen</h1>
          <p className="subtitle">
            Die Übersicht ist deine Arbeitszentrale. Alle wichtigen Bereiche liegen oben als Schnellzugriffe,
            während die Startseite nur noch Orientierung und Bedienhilfe liefert.
          </p>
          <div className="hero-guide">
            <p>
              Wechsle hier direkt zwischen Überblick, Warteschlange und operativer Sicht oder springe gezielt in
              Erfassung, KPIs und Abteilungen. So bleibt der tägliche Arbeitsfluss kompakt und nachvollziehbar.
            </p>
          </div>
        </div>

        <div className="hero-summary-card">
          <span className="hero-summary-label">Heute im Fokus</span>
          <strong className="hero-summary-value">{needsAttentionTickets.length}</strong>
          <span className="hero-summary-text">Tickets mit unmittelbarem Handlungsbedarf</span>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Arbeitszentrale</span>
          <span>•</span>
          <span>{WORKSPACE_TABS.find((tab) => tab.id === activeWorkspace)?.label || "Übersicht"}</span>
        </div>
        <p className="dashboard-context-copy">
          Die Startseite erklärt den Aufbau, hier steuerst du die tägliche Arbeit und springst in vertiefte Bereiche.
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
              helper="Kennzahlen und Verteilungen"
              active={activeWorkspace === "overview"}
              emphasis="primary"
              onClick={() => setActiveWorkspace("overview")}
            />
            <DashboardCommandButton
              label="Warteschlange"
              helper="Filtern, suchen und öffnen"
              active={activeWorkspace === "tickets"}
              emphasis="primary"
              onClick={() => setActiveWorkspace("tickets")}
            />
            <DashboardCommandButton
              label="Nächste Schritte"
              helper="Dringende Fälle priorisieren"
              active={activeWorkspace === "operations"}
              emphasis="primary"
              onClick={() => setActiveWorkspace("operations")}
            />
          </div>
        </div>

        <div className="dashboard-command-section">
          <div className="dashboard-command-heading">
            <span>Sprungmarken</span>
            <p>Öffne bei Bedarf direkt Erfassung, KPIs oder Abteilungen.</p>
          </div>
          <div className="dashboard-command-grid">
            <DashboardCommandButton
              label="Ticket erfassen"
              helper="Neuen Fall anlegen"
              emphasis="secondary"
              onClick={() => navigate("/dashboard/create")}
            />
            <DashboardCommandButton
              label="KPIs"
              helper="Reporting und Trends"
              emphasis="secondary"
              onClick={() => navigate("/dashboard/kpis")}
            />
            <DashboardCommandButton
              label="Abteilungen"
              helper="Verteilung und Ownership"
              emphasis="secondary"
              onClick={() => navigate("/dashboard/departments")}
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
            <StatCard label="Gesamt" value={dashboardStats.total} helper="Gesamte Arbeitslast" accent="neutral" />
            <StatCard label="Triagiert" value={dashboardStats.triaged} helper="Von KI vorqualifiziert" accent="info" />
            <StatCard label="Geprüft" value={dashboardStats.reviewed} helper="Manuell geprüft" accent="warning" />
            <StatCard label="Zugewiesen" value={dashboardStats.assigned} helper="Mit Teamzuweisung" accent="success" />
          </section>

          <section className="workspace-shell">
            <div className="workspace-header">
              <div>
                <p className="workspace-eyebrow">Arbeitsbereiche</p>
                <h2>
                  {activeWorkspace === "overview"
                    ? "Management-Übersicht"
                    : activeWorkspace === "tickets"
                      ? "Ticket-Warteschlange"
                      : "Operative Bearbeitung"}
                </h2>
                <p>
                  {activeWorkspace === "overview"
                    ? "Die wichtigsten Kennzahlen und Verteilungen auf einen Blick."
                    : activeWorkspace === "tickets"
                      ? "Suche, filtere und springe direkt in den passenden Vorgang."
                      : "Konzentriere dich auf Tickets mit hohem Handlungsdruck und aktuelle Aktivitäten."}
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
                  <div className="insight-card">
                    <span className="insight-label">Warteschlange sichtbar</span>
                    <strong>{filteredTickets.length} Tickets</strong>
                    <p>So viele Tickets passen aktuell zu deinen Filtern in der Warteschlange.</p>
                  </div>
                  <div className="insight-card">
                    <span className="insight-label">Prüfabdeckung</span>
                    <strong>{managementMetrics.review_coverage}%</strong>
                    <p>Tickets, die bereits geprüft oder zugewiesen sind.</p>
                  </div>
                  <div className="insight-card">
                    <span className="insight-label">KI-Akzeptanz</span>
                    <strong>{managementMetrics.acceptance_rate}%</strong>
                    <p>Akzeptierte KI-Empfehlungen bezogen auf alle Prüfungen.</p>
                  </div>
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
                    <span className="management-label">Tickets in Prüfung</span>
                    <strong className="management-value">{managementMetrics.reviewed_count}</strong>
                    <span className="management-helper">Bereits manuell geprüfte Tickets</span>
                  </div>
                  <div className="management-card management-card-warning">
                    <span className="management-label">Abteilungen aktiv</span>
                    <strong className="management-value">{activeDepartments.length}</strong>
                    <span className="management-helper">Bereiche mit mindestens einem Ticket</span>
                  </div>
                  <div className="management-card management-card-success">
                    <span className="management-label">KI übernommen</span>
                    <strong className="management-value">{managementMetrics.accepted_ai_count}</strong>
                    <span className="management-helper">Prüfentscheide mit bestätigter Empfehlung</span>
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
                        placeholder="Titel, Beschreibung oder Reporter durchsuchen"
                        value={search}
                        onChange={(event) => setSearch(event.target.value)}
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
                      Die Warteschlange zeigt nur noch passende Tickets. Für neue Fälle oder vertiefte Analysen
                      wechselst du direkt über die Modul-Buttons.
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
                      <p>Reduziere die Filter oder wechsle in die KPI- beziehungsweise Abteilungsansicht.</p>
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
                  subtitle="Tickets mit hoher Priorität oder noch offenem Triage-Status."
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
                  subtitle="Zuletzt angelegte oder geladene Tickets für schnelles Nachfassen."
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
                            <span>Abteilung: {ticket.department || "—"}</span>
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
