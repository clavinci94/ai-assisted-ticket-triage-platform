import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider";
import SectionCard from "../components/SectionCard";
import { fetchDashboardAnalytics, fetchTickets } from "../lib/api";
import {
  BarChart,
  Bar,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

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
      orderedItems.push({ name: key, value, percent: Math.round((value / total) * 100) });
      counts.delete(key);
    }
  });

  Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .forEach(([name, value]) => {
      orderedItems.push({ name, value, percent: Math.round((value / total) * 100) });
    });

  return orderedItems;
}

function StatCard({ label, value, accent, helper }) {
  return (
    <div className={`stat-card stat-card-${accent}`}>
      <div className="stat-card-top">
        <span className="stat-label">{label}</span>
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
        <span className="chart-card-eyebrow">Analyse</span>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
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

const STATUS_COLORS = {
  new: "#94a3b8",
  triaged: "#3b82f6",
  reviewed: "#f59e0b",
  assigned: "#10b981",
  unknown: "#cbd5e1",
};
const CATEGORY_COLORS = ["#4f46e5", "#6366f1", "#22c55e", "#f59e0b", "#0ea5e9", "#f97316"];
const PRIORITY_COLORS = {
  low: "#94a3b8",
  medium: "#3b82f6",
  high: "#f59e0b",
  critical: "#ef4444",
  unknown: "#cbd5e1",
};

function getTicketPriority(ticket) {
  return ticket.final_priority || ticket.analysis?.predicted_priority || "unknown";
}

function getTicketCategory(ticket) {
  return ticket.final_category || ticket.analysis?.predicted_category || "unknown";
}

export default function DashboardKpisPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [tickets, setTickets] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadAnalytics = async () => {
    try {
      const data = await fetchDashboardAnalytics();
      setAnalytics(data);
    } catch (error) {
      showToast({
        type: "error",
        title: "Analyse-Fehler",
        message: error?.response?.data?.detail || "Die Dashboard-Analysen konnten nicht geladen werden.",
      });
    }
  };

  const loadTickets = async () => {
    setLoading(true);
    try {
      const data = await fetchTickets();
      setTickets(data);
      await loadAnalytics();
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTickets();
  }, []);

  const dashboardStats = analytics?.stats || {
    total: tickets.length,
    triaged: 0,
    reviewed: 0,
    assigned: 0,
  };

  const statusDistribution =
    analytics?.status_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => ticket.status, ["new", "triaged", "reviewed", "assigned"]);

  const categoryDistribution =
    analytics?.category_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => getTicketCategory(ticket), ["bug", "feature", "support", "requirement", "question"]);

  const priorityDistribution =
    analytics?.priority_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => getTicketPriority(ticket), ["low", "medium", "high", "critical"]);

  const reviewFunnelData =
    analytics?.review_funnel?.map((item) => ({
      ...item,
      fill:
        item.name === "created"
          ? "#64748b"
          : item.name === "triaged"
          ? "#3b82f6"
          : item.name === "reviewed"
          ? "#f59e0b"
          : "#10b981",
    })) || [];

  return (
    <div className="app-shell dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Reporting</p>
          <h1>Leistungskennzahlen</h1>
          <p className="subtitle">
            KPI-Report für Status, Prioritäten, Prozessverteilung und den aktuellen operativen Gesundheitszustand.
          </p>
        </div>
      </section>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Reporting</span>
          <span>•</span>
          <span>KPIs</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/reports")}>Reports</button>
          <button type="button" onClick={() => navigate("/reports/departments")}>Abteilungen</button>
          <button type="button" onClick={() => navigate("/reports/teams")}>Teams</button>
          <button type="button" onClick={() => navigate("/reports/sla")}>SLA</button>
        </div>
      </section>

      <section className="stats-grid" aria-label="Dashboard KPIs">
        <StatCard label="Gesamt" value={dashboardStats.total} helper="Gesamtes Ticket-Volumen" accent="neutral" />
        <StatCard label="Triagiert" value={dashboardStats.triaged} helper="Von KI bearbeitete Tickets" accent="info" />
        <StatCard label="Geprüft" value={dashboardStats.reviewed} helper="Manuell verifizierte Tickets" accent="warning" />
        <StatCard label="Zugewiesen" value={dashboardStats.assigned} helper="Tickets mit Team-Zuweisung" accent="success" />
      </section>

      <section className="charts-grid" aria-label="Analytics Charts">
        <ChartCard title="Statusverteilung" subtitle="Ticket-Statusverteilung im Betrieb">
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
            <p>Keine Daten verfügbar.</p>
          )}
        </ChartCard>

        <ChartCard title="Kategorienmix" subtitle="Aktuelle Ticket-Kategorien">
          {categoryDistribution.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={categoryDistribution} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]} fill="#4f46e5" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p>Keine Daten verfügbar.</p>
          )}
        </ChartCard>

        <ChartCard title="Prioritäten" subtitle="Ticket-Prioritäten im Überblick">
          {priorityDistribution.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart layout="vertical" data={priorityDistribution} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                <CartesianGrid horizontal={false} stroke="#e5e7eb" />
                <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                <YAxis dataKey="name" type="category" tickLine={false} axisLine={false} width={80} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 8, 8, 0]}>
                  {priorityDistribution.map((entry) => (
                    <Cell key={entry.name} fill={PRIORITY_COLORS[entry.name] || PRIORITY_COLORS.unknown} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p>Keine Daten verfügbar.</p>
          )}
        </ChartCard>
      </section>

      <section className="management-grid" aria-label="Management-Übersicht">
        <ManagementCard
          label="KI-Akzeptanz"
          value={`${analytics?.management_metrics?.acceptance_rate ?? 0}%`}
          helper={`${analytics?.management_metrics?.accepted_ai_count ?? 0} von ${analytics?.management_metrics?.reviewed_count ?? 0} Prüfungen übernommen`}
          accent="info"
        />
        <ManagementCard
          label="Prüfabdeckung"
          value={`${analytics?.management_metrics?.review_coverage ?? 0}%`}
          helper="Anteil bearbeiteter Tickets"
          accent="warning"
        />
        <ManagementCard
          label="Zuweisungsquote"
          value={`${analytics?.management_metrics?.assignment_rate ?? 0}%`}
          helper="Tickets mit Team-Zuordnung"
          accent="success"
        />
      </section>

      {loading && <p>Daten werden geladen...</p>}
    </div>
  );
}
