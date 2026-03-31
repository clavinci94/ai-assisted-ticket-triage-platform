import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { useToast } from "../components/ToastProvider";
import { fetchDashboardAnalytics } from "../lib/api";

function TeamStat({ label, value, helper, accent = "neutral" }) {
  return (
    <div className={`summary-card summary-card-${accent}`}>
      <span className="summary-label">{label}</span>
      <strong>{value}</strong>
      <p>{helper}</p>
    </div>
  );
}

export default function TeamsPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const [analytics, setAnalytics] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchDashboardAnalytics();
        setAnalytics(data);
      } catch (error) {
        showToast({
          type: "error",
          title: "Teamreport konnte nicht geladen werden",
          message: error?.response?.data?.detail || "Die Teamdaten sind momentan nicht verfügbar.",
        });
      }
    }

    load();
  }, [showToast]);

  const teams = analytics?.team_distribution || [];
  const assignees = analytics?.top_assignees || [];
  const activeTeams = teams.filter((team) => team.value > 0);
  const topTeam = teams[0];
  const topCloser = useMemo(
    () =>
      [...assignees].sort((left, right) => right.closed_count - left.closed_count || right.total_count - left.total_count)[0],
    [assignees]
  );

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Reporting</p>
          <h1>Teamreport</h1>
          <p className="subtitle">
            Zeigt aktuelle Teamlast, Zuständigkeiten und dokumentierte Bearbeitungsleistung.
          </p>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Reporting</span>
          <span>•</span>
          <span>Teams</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/reports")}>Reports</button>
          <button type="button" onClick={() => navigate("/reports/kpis")}>KPIs</button>
          <button type="button" onClick={() => navigate("/reports/sla")}>SLA</button>
        </div>
      </section>

      <section className="dashboard-summary-grid">
        <TeamStat label="Aktive Teams" value={activeTeams.length} helper="Teams mit mindestens einem Ticket" accent="info" />
        <TeamStat
          label="Grösste Last"
          value={topTeam?.name || "Noch kein Team"}
          helper={topTeam ? `${topTeam.value} Tickets im Bestand` : "Keine Teamdaten vorhanden"}
          accent="warning"
        />
        <TeamStat
          label="Top Bearbeitung"
          value={topCloser?.name || "Noch keine Bearbeitung"}
          helper={topCloser ? `${topCloser.closed_count} geschlossene Tickets` : "Keine Abschlüsse dokumentiert"}
          accent="success"
        />
      </section>

      <section className="charts-grid">
        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-eyebrow">Teamlast</span>
            <h3>Tickets pro Team</h3>
            <p>Aktueller Bestand nach dokumentierter Zuständigkeit.</p>
          </div>
          <div className="chart-card-body">
            {teams.length ? (
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={teams} layout="vertical" margin={{ top: 8, right: 16, left: 24, bottom: 0 }}>
                  <CartesianGrid vertical={false} stroke="#e5e7eb" />
                  <XAxis type="number" allowDecimals={false} tickLine={false} axisLine={false} />
                  <YAxis dataKey="name" type="category" width={180} tickLine={false} axisLine={false} interval={0} />
                  <Tooltip />
                  <Bar dataKey="value" fill="#0f766e" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <p className="chart-empty">Noch keine Teamverteilung verfügbar.</p>
            )}
          </div>
        </div>

        <div className="chart-card">
          <div className="chart-card-header">
            <span className="chart-card-eyebrow">Bearbeitung</span>
            <h3>Top-Bearbeitungen</h3>
            <p>Dokumentierte Zuständigkeiten mit Fokus auf geschlossene Tickets.</p>
          </div>
          <div className="chart-card-body">
            {assignees.length ? (
              <div className="report-metric-list">
                {assignees.map((item) => (
                  <div key={item.name} className="report-metric-item">
                    <div>
                      <strong>{item.name}</strong>
                      <p>{item.closed_count} geschlossen · {item.active_count} aktiv</p>
                    </div>
                    <span className="report-inline-value">{item.total_count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="chart-empty">Noch keine Bearbeitungsdaten vorhanden.</p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}
