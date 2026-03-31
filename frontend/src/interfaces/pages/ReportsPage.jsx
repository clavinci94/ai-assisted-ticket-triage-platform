import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useToast } from "../components/ToastProvider";
import { fetchDashboardAnalytics } from "../../infrastructure/http/api";

function StatCard({ label, value, helper, accent = "neutral" }) {
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
        <span className="chart-card-eyebrow">Reporting</span>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
      <div className="chart-card-body">{children}</div>
    </div>
  );
}

function ReportLinkCard({ title, text, onClick }) {
  return (
    <button type="button" className="report-link-card" onClick={onClick}>
      <strong>{title}</strong>
      <p>{text}</p>
      <span>Bereich öffnen</span>
    </button>
  );
}

function MetricList({ title, items, emptyMessage, renderLabel, renderMeta }) {
  return (
    <div className="report-metric-card">
      <div className="report-metric-card-header">
        <span className="chart-card-eyebrow">Detailansicht</span>
        <h3>{title}</h3>
      </div>

      {items.length ? (
        <div className="report-metric-list">
          {items.map((item) => (
            <div key={renderLabel(item)} className="report-metric-item">
              <div>
                <strong>{renderLabel(item)}</strong>
                <p>{renderMeta(item)}</p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="chart-empty">{emptyMessage}</p>
      )}
    </div>
  );
}

export default function ReportsPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    async function loadAnalytics() {
      try {
        setLoading(true);
        const data = await fetchDashboardAnalytics();
        setAnalytics(data);
      } catch (error) {
        showToast({
          type: "error",
          title: "Reporting konnte nicht geladen werden",
          message: error?.response?.data?.detail || "Die Reporting-Daten sind momentan nicht verfügbar.",
        });
      } finally {
        setLoading(false);
      }
    }

    loadAnalytics();
  }, [showToast]);

  const stats = analytics?.stats || { total: 0, triaged: 0, reviewed: 0, assigned: 0, closed: 0 };
  const slaMetrics = analytics?.sla_metrics || {
    total_with_sla: 0,
    in_sla: 0,
    due_soon: 0,
    overdue: 0,
    breached: 0,
  };
  const volumeTrend = analytics?.ticket_volume_over_time || [];
  const backlogTrend = analytics?.backlog_development || [];
  const priorityCycle = analytics?.processing_time_by_priority || [];
  const topAssignees = analytics?.top_assignees || [];
  const teamDistribution = analytics?.team_distribution || [];

  const activeTeamCount = useMemo(
    () => teamDistribution.filter((item) => item.value > 0).length,
    [teamDistribution]
  );
  const hottestTeam = teamDistribution[0]?.name || "Noch kein Team";
  const topAssignee = topAssignees[0]?.name || "Noch keine Bearbeitung";

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Reporting & Governance</p>
          <h1>Berichts- und Analysezentrale</h1>
          <p className="subtitle">
            Dieser Bereich bündelt Volumen, Backlog, SLA-Lage und Ownership in einer gemeinsamen Reporting-Sicht.
          </p>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Reporting</span>
          <span>•</span>
          <span>Übersicht</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/reports/kpis")}>KPIs</button>
          <button type="button" onClick={() => navigate("/reports/departments")}>Abteilungen</button>
          <button type="button" onClick={() => navigate("/reports/teams")}>Teams</button>
          <button type="button" onClick={() => navigate("/reports/sla")}>SLA</button>
        </div>
      </section>

      <section className="stats-grid" aria-label="Reporting-Überblick">
        <StatCard label="Gesamtbestand" value={stats.total} helper="Alle Tickets im Reporting" accent="neutral" />
        <StatCard label="Geschlossen" value={stats.closed} helper="Bereits abgeschlossene Vorgänge" accent="success" />
        <StatCard label="SLA-Verletzungen" value={slaMetrics.breached} helper="Bereits als verletzt markiert" accent="danger" />
        <StatCard label="Aktive Teams" value={activeTeamCount} helper={`Höchste Auslastung: ${hottestTeam}`} accent="info" />
        <StatCard label="Top-Bearbeitung" value={topAssignee} helper="Aktuell meist dokumentierte Zuständigkeit" accent="warning" />
      </section>

      <section className="report-link-grid" aria-label="Reporting-Module">
        <ReportLinkCard
          title="KPI-Detail"
          text="Status, Prioritäten und Prozessverteilung im Detail betrachten."
          onClick={() => navigate("/reports/kpis")}
        />
        <ReportLinkCard
          title="Abteilungsreport"
          text="Ownership und Ticketlast nach Fachbereich analysieren."
          onClick={() => navigate("/reports/departments")}
        />
        <ReportLinkCard
          title="Teamreport"
          text="Teamlast und Bearbeitungsfokus pro Squad oder Service Desk prüfen."
          onClick={() => navigate("/reports/teams")}
        />
        <ReportLinkCard
          title="SLA-Report"
          text="Due-Soon-, Overdue- und Breach-Signale zentral steuern."
          onClick={() => navigate("/reports/sla")}
        />
      </section>

      <section className="charts-grid" aria-label="Reporting Charts">
        <ChartCard title="Ticketvolumen über Zeit" subtitle="Neu angelegte Tickets pro Tag">
          {volumeTrend.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={volumeTrend} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Noch keine Zeitreihendaten verfügbar.</p>
          )}
        </ChartCard>

        <ChartCard title="Backlog-Entwicklung" subtitle="Neu eingegangene versus geschlossene Tickets">
          {backlogTrend.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={backlogTrend} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="backlog" stroke="#0f766e" strokeWidth={3} dot={{ r: 3 }} />
                <Line type="monotone" dataKey="closed" stroke="#16a34a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Noch keine Backlog-Daten verfügbar.</p>
          )}
        </ChartCard>

        <ChartCard title="Bearbeitungszeit nach Priorität" subtitle="Durchschnittliche Stunden bis zur letzten relevanten Aktivität">
          {priorityCycle.length ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={priorityCycle} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#e5e7eb" />
                <XAxis dataKey="priority" tickLine={false} axisLine={false} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} />
                <Tooltip />
                <Bar dataKey="average_hours" fill="#7c3aed" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Noch keine Prozesszeiten verfügbar.</p>
          )}
        </ChartCard>
      </section>

      <section className="report-support-grid" aria-label="Reporting Details">
        <MetricList
          title="Top-Bearbeitungen"
          items={topAssignees.slice(0, 5)}
          emptyMessage="Es sind noch keine Bearbeitungsdaten vorhanden."
          renderLabel={(item) => item.name}
          renderMeta={(item) => `${item.closed_count} geschlossen · ${item.active_count} aktiv · ${item.total_count} total`}
        />

        <MetricList
          title="Aktive Teams"
          items={teamDistribution.slice(0, 5)}
          emptyMessage="Noch keine Teamzuordnung verfügbar."
          renderLabel={(item) => item.name}
          renderMeta={(item) => `${item.value} Tickets im aktuellen Bestand`}
        />
      </section>

      {loading ? <p>Daten werden geladen...</p> : null}
    </div>
  );
}
