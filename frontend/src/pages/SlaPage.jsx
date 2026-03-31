import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import SlaBadge from "../components/SlaBadge";
import { useToast } from "../components/ToastProvider";
import { fetchDashboardAnalytics, fetchTickets } from "../lib/api";

function SlaStatCard({ label, value, helper, accent = "neutral" }) {
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

function normalizeTicketDueState(ticket) {
  if (ticket.sla_breached) {
    return "verletzt";
  }

  if (!ticket.due_at) {
    return "ohne frist";
  }

  const dueDate = new Date(ticket.due_at);
  if (Number.isNaN(dueDate.getTime())) {
    return "unklar";
  }

  if (dueDate.getTime() < Date.now()) {
    return "überfällig";
  }

  if (dueDate.getTime() - Date.now() <= 24 * 60 * 60 * 1000) {
    return "bald fällig";
  }

  return "im rahmen";
}

export default function SlaPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [analytics, setAnalytics] = useState(null);
  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    async function load() {
      try {
        const [analyticsData, ticketsData] = await Promise.all([
          fetchDashboardAnalytics(),
          fetchTickets(),
        ]);
        setAnalytics(analyticsData);
        setTickets(ticketsData);
      } catch (error) {
        showToast({
          type: "error",
          title: "SLA-Report konnte nicht geladen werden",
          message: error?.response?.data?.detail || "Die SLA-Daten sind momentan nicht verfügbar.",
        });
      }
    }

    load();
  }, [showToast]);

  const slaMetrics = analytics?.sla_metrics || {
    total_with_sla: 0,
    in_sla: 0,
    due_soon: 0,
    overdue: 0,
    breached: 0,
  };

  const slaChartData = [
    { name: "Im SLA", value: slaMetrics.in_sla },
    { name: "Bald fällig", value: slaMetrics.due_soon },
    { name: "Überfällig", value: slaMetrics.overdue },
    { name: "Verletzt", value: slaMetrics.breached },
  ];

  const atRiskTickets = useMemo(
    () =>
      tickets
        .filter((ticket) => ticket.sla_breached || ticket.due_at)
        .filter((ticket) => ["verletzt", "überfällig", "bald fällig"].includes(normalizeTicketDueState(ticket)))
        .slice(0, 8),
    [tickets]
  );

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Reporting</p>
          <h1>SLA & Fristen</h1>
          <p className="subtitle">
            Fristverletzungen, bald fällige Tickets und SLA-Risiken in einer operativen Übersicht.
          </p>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Reporting</span>
          <span>•</span>
          <span>SLA</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/reports")}>Reports</button>
          <button type="button" onClick={() => navigate("/reports/teams")}>Teams</button>
          <button type="button" onClick={() => navigate("/reports/kpis")}>KPIs</button>
        </div>
      </section>

      <section className="stats-grid">
        <SlaStatCard label="SLA-Tickets" value={slaMetrics.total_with_sla} helper="Fälle mit Fristbezug oder Breach-Flag" accent="neutral" />
        <SlaStatCard label="Im SLA" value={slaMetrics.in_sla} helper="Tickets innerhalb der dokumentierten Frist" accent="success" />
        <SlaStatCard label="Bald fällig" value={slaMetrics.due_soon} helper="Frist endet in den nächsten 24 Stunden" accent="warning" />
        <SlaStatCard label="Überfällig" value={slaMetrics.overdue} helper="Frist überschritten, aber noch nicht als Breach markiert" accent="danger" />
        <SlaStatCard label="Verletzt" value={slaMetrics.breached} helper="Bereits dokumentierte SLA-Verletzungen" accent="danger" />
      </section>

      <section className="charts-grid">
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-eyebrow">SLA-Lage</span>
            <h3>SLA-Verteilung</h3>
            <p>Aggregierte Sicht auf Fristlage und Breach-Signale.</p>
          </div>
          <div className="chart-card-body">
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={slaChartData} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="name" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="value" fill="#dc2626" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-eyebrow">Risikofälle</span>
            <h3>Tickets mit unmittelbarem Fristfokus</h3>
            <p>Verletzte, überfällige oder bald fällige Vorgänge.</p>
          </div>
          <div className="chart-card-body">
            {atRiskTickets.length ? (
              <div className="report-ticket-list">
                {atRiskTickets.map((ticket) => (
                  <Link key={ticket.ticket_id} to={`/tickets/${ticket.ticket_id}`} className="report-ticket-row">
                    <div>
                      <strong>{ticket.title}</strong>
                      <p>{ticket.department || "Bank-IT Support"}</p>
                    </div>
                    <SlaBadge dueAt={ticket.due_at} breached={ticket.sla_breached} />
                  </Link>
                ))}
              </div>
            ) : (
              <p className="chart-empty">Derzeit gibt es keine kritischen SLA-Fälle.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
