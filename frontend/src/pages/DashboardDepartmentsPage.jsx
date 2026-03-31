import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { BarChart, Bar, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { fetchDashboardAnalytics, fetchTickets } from "../lib/api";
import { useToast } from "../components/ToastProvider";
import { DEPARTMENTS, normalizeDepartment } from "../lib/departments";

const DEPARTMENT_COLOR = "#6366f1";

function normalizeLabel(value) {
  return String(value || "unknown").toLowerCase();
}

function buildDistributionFromAccessor(tickets, accessor, orderedLabels = [], includeEmptyLabels = false) {
  const counts = new Map();

  tickets.forEach((ticket) => {
    const key = normalizeLabel(normalizeDepartment(accessor(ticket)));
    counts.set(key, (counts.get(key) || 0) + 1);
  });

  const orderedItems = [];
  const total = tickets.length || 1;

  orderedLabels.forEach((label) => {
    const normalized = normalizeLabel(label);
    const value = counts.get(normalized) || 0;
    if (value > 0 || includeEmptyLabels) {
      orderedItems.push({ name: label, value, percent: Math.round((value / total) * 100) });
    }
    counts.delete(normalized);
  });

  Array.from(counts.entries())
    .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
    .forEach(([name, value]) => {
      orderedItems.push({ name, value, percent: Math.round((value / total) * 100) });
    });

  return orderedItems;
}

function ChartCard({ title, subtitle, children }) {
  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <div>
          <span className="chart-card-eyebrow">Abteilungsanalyse</span>
          <h3>{title}</h3>
          <p>{subtitle}</p>
        </div>
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
}

export default function DashboardDepartmentsPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [tickets, setTickets] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  async function loadAnalytics() {
    try {
      const data = await fetchDashboardAnalytics();
      setAnalytics(data);
    } catch (err) {
      showToast({
        type: "error",
        title: "Analytics laden fehlgeschlagen",
        message: err?.response?.data?.detail || "Abteilungsdaten konnten nicht geladen werden.",
      });
    }
  }

  async function loadTickets() {
    try {
      setLoading(true);
      const data = await fetchTickets();
      setTickets(data);
      await loadAnalytics();
    } catch (err) {
      showToast({
        type: "error",
        title: "Tickets laden fehlgeschlagen",
        message: err?.response?.data?.detail || "Tickets konnten nicht geladen werden.",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
  }, []);

  const departmentDistribution =
    analytics?.department_distribution ||
    buildDistributionFromAccessor(tickets, (ticket) => ticket.department, DEPARTMENTS, true);

  const activeDepartmentCount = useMemo(
    () => departmentDistribution.filter((item) => item.value > 0).length,
    [departmentDistribution]
  );

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Banken-Übersicht</p>
          <h1>Abteilungsübersicht</h1>
          <p className="subtitle">
            Hier findest du die Ticketverteilung nach Fachbereich und erkennst schnell, welche Bank-Teams aktuell
            die höchste Auslastung haben.
          </p>
          <div className="hero-guide">
            <p>Diese Seite ist der zentrale Einstieg für deine Abteilungssteuerung.</p>
            <ul>
              <li>Nutze die Grafik, um kritische Abteilungen zu identifizieren.</li>
              <li>Prüfe die Anzahl aktiver Tickets je Bereich.</li>
              <li>Wechsle bei Bedarf direkt zurück zu Dashboard oder KPI-Ansicht.</li>
            </ul>
          </div>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Dashboard</span>
          <span>•</span>
          <span>Abteilungen</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button type="button" onClick={() => navigate("/dashboard/kpis")}>KPIs</button>
          <button type="button" onClick={() => navigate("/dashboard/create")}>Ticket erstellen</button>
        </div>
      </section>

      <section className="dashboard-summary-grid">
        <div className="summary-card">
          <span className="summary-label">Gesamte Tickets</span>
          <strong>{tickets.length}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-label">Definierte Abteilungen</span>
          <strong>{DEPARTMENTS.length}</strong>
        </div>
        <div className="summary-card">
          <span className="summary-label">Aktive Abteilungen</span>
          <strong>{activeDepartmentCount}</strong>
        </div>
      </section>

      <section className="charts-grid" aria-label="Abteilungsdiagramm">
        <ChartCard
          title="Ticketverteilung nach Abteilung"
          subtitle="Welche Bankbereiche betreuen aktuell die meisten Tickets"
        >
          {departmentDistribution.length ? (
            <ResponsiveContainer width="100%" height={420}>
              <BarChart
                data={departmentDistribution}
                layout="vertical"
                margin={{ top: 8, right: 16, left: 24, bottom: 0 }}
              >
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={170}
                  tickLine={false}
                  axisLine={false}
                  interval={0}
                />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 8, 8, 0]} fill={DEPARTMENT_COLOR}>
                  {departmentDistribution.map((entry) => (
                    <Cell key={entry.name} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Keine Abteilungsdaten verfügbar.</p>
          )}
        </ChartCard>
      </section>
    </div>
  );
}
