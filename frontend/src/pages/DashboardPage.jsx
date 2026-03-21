import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  PieChart,
  Pie,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import MessageBanner from "../components/MessageBanner";
import SectionCard from "../components/SectionCard";
import TicketList from "../components/TicketList";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import Badge from "../components/Badge";
import { fetchTickets, triageTicket } from "../lib/api";

const initialTicketForm = {
  title: "",
  description: "",
  reporter: "",
  source: "internal",
};

const STATUS_COLORS = {
  new: "#94a3b8",
  triaged: "#3b82f6",
  reviewed: "#f59e0b",
  assigned: "#10b981",
  unknown: "#cbd5e1",
};

const CATEGORY_COLORS = ["#3b82f6", "#8b5cf6", "#f59e0b", "#10b981", "#ef4444", "#64748b"];
const PRIORITY_COLORS = {
  low: "#94a3b8",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
  unknown: "#cbd5e1",
};

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

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div>
          <span className="chart-card-eyebrow">Operational Insights</span>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
}

function EmptyChartState() {
  return <p className="chart-empty">Noch keine Daten verfügbar.</p>;
}

function ManagementCard({ label, value, helper, accent = "neutral" }) {
  return (
    <div className={`management-card management-card-${accent}`}>
      <span className="management-label">{label}</span>
      <strong className="management-value">{value}</strong>
      <span className="management-helper">{helper}</span>
    </div>
  );
}

function OperationalPanel({ title, subtitle, children }) {
  return (
    <div className="operational-panel">
      <div className="operational-panel-header">
        <span className="operational-panel-eyebrow">Operational View</span>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="operational-panel-body">{children}</div>
    </div>
  );
}

function normalizeLabel(value) {
  return String(value || "unknown").toLowerCase();
}

function buildDistributionFromAccessor(tickets, accessor, orderedLabels = []) {
  const counts = new Map();

  tickets.forEach((ticket) => {
    const normalized = normalizeLabel(accessor(ticket));
    counts.set(normalized, (counts.get(normalized) || 0) + 1);
  });

  const orderedItems = [];
  const total = tickets.length || 1;

  orderedLabels.forEach((label) => {
    const key = normalizeLabel(label);
    if (counts.has(key)) {
      const value = counts.get(key);
      orderedItems.push({
        name: key,
        value,
        percent: Math.round((value / total) * 100),
      });
      counts.delete(key);
    }
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
  return ticket.final_priority || ticket.analysis?.predicted_priority || "unknown";
}

function getTicketCategory(ticket) {
  return ticket.final_category || ticket.analysis?.predicted_category || "unknown";
}

export default function DashboardPage() {
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [ticketForm, setTicketForm] = useState(initialTicketForm);

  const [loadingTickets, setLoadingTickets] = useState(false);
  const [submittingTriage, setSubmittingTriage] = useState(false);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadTickets() {
    try {
      setLoadingTickets(true);
      setError("");
      const data = await fetchTickets();
      setTickets(data);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load tickets.");
    } finally {
      setLoadingTickets(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  const dashboardStats = useMemo(() => {
    const total = tickets.length;
    const triaged = tickets.filter((ticket) => ticket.status === "triaged").length;
    const reviewed = tickets.filter((ticket) => ticket.status === "reviewed").length;
    const assigned = tickets.filter((ticket) => ticket.status === "assigned").length;

    return {
      total,
      triaged,
      reviewed,
      assigned,
    };
  }, [tickets]);

  const statusDistribution = useMemo(() => {
    return buildDistributionFromAccessor(
      tickets,
      (ticket) => ticket.status,
      ["new", "triaged", "reviewed", "assigned"]
    );
  }, [tickets]);

  const categoryDistribution = useMemo(() => {
    return buildDistributionFromAccessor(
      tickets,
      (ticket) => getTicketCategory(ticket),
      ["bug", "feature", "support", "requirement", "question"]
    );
  }, [tickets]);

  const priorityDistribution = useMemo(() => {
    return buildDistributionFromAccessor(
      tickets,
      (ticket) => getTicketPriority(ticket),
      ["low", "medium", "high", "critical"]
    );
  }, [tickets]);

  const managementMetrics = useMemo(() => {
    const total = tickets.length;
    const reviewedOrBeyond = tickets.filter(
      (ticket) => ticket.status === "reviewed" || ticket.status === "assigned"
    ).length;

    const assigned = tickets.filter((ticket) => ticket.status === "assigned").length;

    const reviewedTickets = tickets.filter((ticket) => ticket.decision);
    const acceptedAiCount = reviewedTickets.filter(
      (ticket) => ticket.decision?.accepted_ai_suggestion === true
    ).length;

    const acceptanceRate = reviewedTickets.length
      ? Math.round((acceptedAiCount / reviewedTickets.length) * 100)
      : 0;

    const assignmentRate = total ? Math.round((assigned / total) * 100) : 0;
    const reviewCoverage = total ? Math.round((reviewedOrBeyond / total) * 100) : 0;

    return {
      reviewedCount: reviewedTickets.length,
      acceptedAiCount,
      acceptanceRate,
      assignmentRate,
      reviewCoverage,
    };
  }, [tickets]);

  const reviewFunnelData = useMemo(() => {
    const total = tickets.length;
    const triaged = tickets.filter((ticket) => ticket.status === "triaged").length;
    const reviewed = tickets.filter(
      (ticket) => ticket.status === "reviewed" || ticket.status === "assigned"
    ).length;
    const assigned = tickets.filter((ticket) => ticket.status === "assigned").length;

    return [
      { name: "created", value: total, fill: "#64748b" },
      { name: "triaged", value: triaged, fill: "#3b82f6" },
      { name: "reviewed", value: reviewed, fill: "#f59e0b" },
      { name: "assigned", value: assigned, fill: "#10b981" },
    ];
  }, [tickets]);

  const aiAcceptanceData = useMemo(() => {
    const reviewedTickets = tickets.filter((ticket) => ticket.decision);
    const accepted = reviewedTickets.filter(
      (ticket) => ticket.decision?.accepted_ai_suggestion === true
    ).length;
    const adjusted = Math.max(reviewedTickets.length - accepted, 0);

    return [
      { name: "accepted", value: accepted },
      { name: "adjusted", value: adjusted },
    ];
  }, [tickets]);

  const filteredTickets = useMemo(() => {
    return tickets.filter((ticket) => {
      const normalizedSearch = search.toLowerCase();

      const matchesSearch =
        (ticket.title || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.description || "").toLowerCase().includes(normalizedSearch) ||
        (ticket.reporter || "").toLowerCase().includes(normalizedSearch);

      const matchesStatus = statusFilter === "all" ? true : ticket.status === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [tickets, search, statusFilter]);

  const recentTickets = useMemo(() => {
    return [...tickets].reverse().slice(0, 5);
  }, [tickets]);

  const needsAttentionTickets = useMemo(() => {
    return tickets
      .filter((ticket) => {
        const priority = getTicketPriority(ticket);
        return priority === "high" || priority === "critical" || ticket.status === "triaged";
      })
      .sort((a, b) => {
        const rank = { critical: 4, high: 3, medium: 2, low: 1, unknown: 0 };
        return rank[getTicketPriority(b)] - rank[getTicketPriority(a)];
      })
      .slice(0, 5);
  }, [tickets]);

  async function handleTriageSubmit(e) {
    e.preventDefault();

    try {
      setSubmittingTriage(true);
      setError("");
      setSuccess("");

      const result = await triageTicket(ticketForm);
      await loadTickets();
      setTicketForm(initialTicketForm);
      setSuccess("Ticket was created and triaged successfully.");
      navigate(`/tickets/${result.ticket_id}`);
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to triage ticket.");
    } finally {
      setSubmittingTriage(false);
    }
  }

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Capstone Project</p>
          <h1>AI-assisted Requirements & Ticket Triage Platform</h1>
          <p className="subtitle">
            AI assistiert, Business Rules kontrollieren, der Mensch validiert.
          </p>
        </div>

        <div className="hero-summary-card">
          <span className="hero-summary-label">Platform Snapshot</span>
          <strong className="hero-summary-value">{dashboardStats.total}</strong>
          <span className="hero-summary-text">Total tickets currently tracked</span>
        </div>
      </header>

      <MessageBanner type="error" message={error} />
      <MessageBanner type="success" message={success} />

      <section className="stats-grid" aria-label="Dashboard KPIs">
        <StatCard
          label="Total Tickets"
          value={dashboardStats.total}
          helper="Overall workload"
          accent="neutral"
        />
        <StatCard
          label="Triaged"
          value={dashboardStats.triaged}
          helper="AI-processed queue"
          accent="info"
        />
        <StatCard
          label="Reviewed"
          value={dashboardStats.reviewed}
          helper="Human-validated"
          accent="warning"
        />
        <StatCard
          label="Assigned"
          value={dashboardStats.assigned}
          helper="Ready for execution"
          accent="success"
        />
      </section>

      <section className="management-grid" aria-label="Management Summary">
        <ManagementCard
          label="AI Acceptance Rate"
          value={`${managementMetrics.acceptanceRate}%`}
          helper={`${managementMetrics.acceptedAiCount} accepted of ${managementMetrics.reviewedCount} reviewed`}
          accent="info"
        />
        <ManagementCard
          label="Review Coverage"
          value={`${managementMetrics.reviewCoverage}%`}
          helper="Tickets reviewed or assigned"
          accent="warning"
        />
        <ManagementCard
          label="Assignment Rate"
          value={`${managementMetrics.assignmentRate}%`}
          helper="Tickets with explicit team ownership"
          accent="success"
        />
      </section>

      <section className="insight-strip">
        <div className="insight-card">
          <span className="insight-label">Workflow Status</span>
          <strong>
            {dashboardStats.assigned} assigned / {dashboardStats.total} total
          </strong>
          <p>Shows how much of the ticket flow already reached explicit team ownership.</p>
        </div>

        <div className="insight-card">
          <span className="insight-label">Review Pipeline</span>
          <strong>
            {dashboardStats.reviewed + dashboardStats.assigned} reviewed or beyond
          </strong>
          <p>Indicates how many tickets already passed manual validation.</p>
        </div>

        <div className="insight-card">
          <span className="insight-label">Queue Visibility</span>
          <strong>{filteredTickets.length} visible in current filter</strong>
          <p>Reflects search and status filtering in the list view.</p>
        </div>
      </section>

      <section className="charts-grid" aria-label="Analytics Charts">
        <ChartCard
          title="Status Distribution"
          subtitle="Current operational state across the ticket workflow."
        >
          {statusDistribution.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={statusDistribution} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {statusDistribution.map((entry) => (
                    <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || STATUS_COLORS.unknown} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
        </ChartCard>

        <ChartCard
          title="Category Mix"
          subtitle="Observed ticket categories based on final or predicted labels."
        >
          {categoryDistribution.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={categoryDistribution}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={58}
                  outerRadius={92}
                  paddingAngle={3}
                >
                  {categoryDistribution.map((entry, index) => (
                    <Cell
                      key={entry.name}
                      fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
          <div className="chart-legend">
            {categoryDistribution.map((entry, index) => (
              <div key={entry.name} className="chart-legend-item">
                <span
                  className="chart-legend-dot"
                  style={{ backgroundColor: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }}
                />
                <span className="chart-legend-label">{entry.name}</span>
                <span className="chart-legend-value">{entry.value}</span>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard
          title="Priority Levels"
          subtitle="Current priority distribution across the ticket inventory."
        >
          {priorityDistribution.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart
                data={priorityDistribution}
                layout="vertical"
                margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
              >
                <CartesianGrid horizontal={false} stroke="#e5e7eb" />
                <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                <YAxis
                  dataKey="name"
                  type="category"
                  tickLine={false}
                  axisLine={false}
                  width={70}
                />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {priorityDistribution.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={PRIORITY_COLORS[entry.name] || PRIORITY_COLORS.unknown}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
        </ChartCard>
      </section>

      <section className="charts-grid management-charts-grid" aria-label="Management Analytics">
        <ChartCard
          title="Review Funnel"
          subtitle="Progression from created tickets through triage, review and assignment."
        >
          {reviewFunnelData.some((item) => item.value > 0) ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={reviewFunnelData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {reviewFunnelData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
        </ChartCard>

        <ChartCard
          title="AI Acceptance"
          subtitle="How often human reviewers accepted the AI recommendation."
        >
          {aiAcceptanceData.some((item) => item.value > 0) ? (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={aiAcceptanceData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={58}
                  outerRadius={92}
                  paddingAngle={3}
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#f59e0b" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <EmptyChartState />
          )}
          <div className="chart-legend">
            {aiAcceptanceData.map((entry, index) => (
              <div key={entry.name} className="chart-legend-item">
                <span
                  className="chart-legend-dot"
                  style={{ backgroundColor: index === 0 ? "#10b981" : "#f59e0b" }}
                />
                <span className="chart-legend-label">{entry.name}</span>
                <span className="chart-legend-value">{entry.value}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </section>

      <section className="operations-grid" aria-label="Operational Panels">
        <OperationalPanel
          title="Needs Attention"
          subtitle="High-priority or still triaged tickets that likely need the next action soon."
        >
          {needsAttentionTickets.length ? (
            <div className="ops-list">
              {needsAttentionTickets.map((ticket) => (
                <button
                  key={ticket.ticket_id}
                  className="ops-list-item"
                  onClick={() => navigate(`/tickets/${ticket.ticket_id}`)}
                >
                  <div className="ops-list-top">
                    <strong>{ticket.title}</strong>
                    <Badge value={getTicketPriority(ticket)} type="priority" />
                  </div>
                  <div className="ops-list-meta">
                    <Badge value={ticket.status} type="status" />
                    <Badge value={getTicketCategory(ticket)} type="category" />
                  </div>
                  <p>{ticket.description || "No description available."}</p>
                </button>
              ))}
            </div>
          ) : (
            <p className="ops-empty">No urgent tickets currently flagged.</p>
          )}
        </OperationalPanel>

        <OperationalPanel
          title="Recent Activity"
          subtitle="Most recently created or loaded tickets for fast follow-up navigation."
        >
          {recentTickets.length ? (
            <div className="ops-list">
              {recentTickets.map((ticket) => (
                <button
                  key={ticket.ticket_id}
                  className="ops-list-item"
                  onClick={() => navigate(`/tickets/${ticket.ticket_id}`)}
                >
                  <div className="ops-list-top">
                    <strong>{ticket.title}</strong>
                    <Badge value={ticket.status} type="status" />
                  </div>
                  <div className="ops-list-meta">
                    <span>Reporter: {ticket.reporter || "—"}</span>
                    <span>Source: {ticket.source || "—"}</span>
                  </div>
                  <p>{ticket.description || "No description available."}</p>
                </button>
              ))}
            </div>
          ) : (
            <p className="ops-empty">No recent tickets available yet.</p>
          )}
        </OperationalPanel>
      </section>

      <main className="layout dashboard-layout">
        <div className="left-column">
          <SectionCard title="Create & Triage Ticket">
            <form className="form" onSubmit={handleTriageSubmit}>
              <label>
                Title
                <input
                  value={ticketForm.title}
                  onChange={(e) => setTicketForm({ ...ticketForm, title: e.target.value })}
                  required
                />
              </label>

              <label>
                Description
                <textarea
                  rows="5"
                  value={ticketForm.description}
                  onChange={(e) =>
                    setTicketForm({ ...ticketForm, description: e.target.value })
                  }
                  required
                />
              </label>

              <label>
                Reporter
                <input
                  value={ticketForm.reporter}
                  onChange={(e) => setTicketForm({ ...ticketForm, reporter: e.target.value })}
                />
              </label>

              <label>
                Source
                <input
                  value={ticketForm.source}
                  onChange={(e) => setTicketForm({ ...ticketForm, source: e.target.value })}
                />
              </label>

              <button type="submit" disabled={submittingTriage}>
                {submittingTriage ? "Submitting..." : "Create & Triage"}
              </button>
            </form>
          </SectionCard>
        </div>

        <div className="right-column">
          <SectionCard title="Tickets">
            <div className="toolbar toolbar-elevated">
              <input
                className="toolbar-input"
                placeholder="Search tickets..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <select
                className="toolbar-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="new">new</option>
                <option value="triaged">triaged</option>
                <option value="reviewed">reviewed</option>
                <option value="assigned">assigned</option>
              </select>
            </div>

            <TicketList tickets={filteredTickets} loading={loadingTickets} emptyTitle="No tickets match the current view" emptyMessage="Try a different filter or create a new ticket to seed the queue."
              loading={loadingTickets}
              selectedTicketId={null}
            />
          </SectionCard>
        </div>
      </main>
    </div>
  );
}
