import { useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
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
import { useSetPageHeading } from "../components/PageHeadingContext";
import ReportsTabs from "../components/ReportsTabs";
import { useToast } from "../components/ToastProvider";
import { fetchDashboardAnalytics } from "../../infrastructure/http/api";

const RANGES = [
  { key: "7d", label: "7T", days: 7 },
  { key: "30d", label: "30T", days: 30 },
  { key: "90d", label: "90T", days: 90 },
];

function lastN(list, n) {
  if (!Array.isArray(list)) return [];
  return list.slice(Math.max(0, list.length - n));
}

function numericAggregates(series, key) {
  const values = (series || []).map((row) => Number(row?.[key] ?? 0)).filter((v) => Number.isFinite(v));
  if (values.length === 0) return { avg: 0, median: 0, peak: 0 };
  const sorted = [...values].sort((a, b) => a - b);
  const avg = Math.round(values.reduce((sum, v) => sum + v, 0) / values.length);
  const median = Math.round(sorted[Math.floor(sorted.length / 2)]);
  const peak = Math.max(...values);
  return { avg, median, peak };
}

function ChartPanel({ title, series, valueKey, children }) {
  const aggregates = useMemo(() => numericAggregates(series, valueKey), [series, valueKey]);
  return (
    <section className="report-panel">
      <header className="report-panel-head">
        <h2>{title}</h2>
        <div className="report-panel-aggregates">
          <div>
            <span>∅</span>
            <strong className="tabular-nums">{aggregates.avg}</strong>
          </div>
          <div>
            <span>Median</span>
            <strong className="tabular-nums">{aggregates.median}</strong>
          </div>
          <div>
            <span>Peak</span>
            <strong className="tabular-nums">{aggregates.peak}</strong>
          </div>
        </div>
      </header>
      <div className="report-panel-body">{children}</div>
    </section>
  );
}

function DetailList({ title, rows, formatLabel, formatMeta, emptyLabel }) {
  return (
    <section className="report-detail-panel">
      <header className="report-detail-head">
        <h2>{title}</h2>
        <span className="tabular-nums">{rows.length}</span>
      </header>
      <ul className="report-detail-list">
        {rows.length === 0 ? (
          <li className="report-detail-empty">{emptyLabel}</li>
        ) : (
          rows.map((row, i) => (
            <li key={i} className="report-detail-row">
              <span className="report-detail-label">{formatLabel(row)}</span>
              <span className="report-detail-meta tabular-nums">{formatMeta(row)}</span>
            </li>
          ))
        )}
      </ul>
    </section>
  );
}

export default function ReportsPage() {
  const { showToast } = useToast();
  const [analytics, setAnalytics] = useState(null);
  const [range, setRange] = useState("30d");
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [teamFilter, setTeamFilter] = useState("all");

  useEffect(() => {
    let cancelled = false;
    fetchDashboardAnalytics()
      .then((data) => {
        if (!cancelled) setAnalytics(data);
      })
      .catch(() => {
        if (!cancelled) {
          showToast({
            type: "error",
            title: "Reporting konnte nicht geladen werden",
            message: "Die Reporting-Daten sind momentan nicht verfügbar.",
          });
        }
      });
    return () => {
      cancelled = true;
    };
  }, [showToast]);

  useSetPageHeading("Reports");

  const rangeDays = RANGES.find((r) => r.key === range)?.days || 30;
  const volumeTrend = useMemo(
    () => lastN(analytics?.ticket_volume_over_time || [], rangeDays),
    [analytics, rangeDays],
  );
  const backlogTrend = useMemo(
    () => lastN(analytics?.backlog_development || [], rangeDays),
    [analytics, rangeDays],
  );

  const priorityCycle = useMemo(() => {
    const rows = analytics?.processing_time_by_priority || [];
    if (priorityFilter === "all") return rows;
    return rows.filter((row) => String(row.priority).toLowerCase() === priorityFilter);
  }, [analytics, priorityFilter]);

  const topAssignees = analytics?.top_assignees || [];
  const teamDistribution = useMemo(() => {
    const all = analytics?.team_distribution || [];
    if (teamFilter === "all") return all;
    return all.filter((row) => row.name === teamFilter);
  }, [analytics, teamFilter]);

  const teamOptions = useMemo(() => {
    const rows = analytics?.team_distribution || [];
    return rows.map((r) => r.name).filter(Boolean);
  }, [analytics]);

  return (
    <div className="app-shell reports-shell">
      <ReportsTabs />

      <div className="reports-filter-bar">
        <div className="segmented">
          {RANGES.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`segmented-option ${range === item.key ? "active" : ""}`}
              onClick={() => setRange(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>

        <label className="filter-chip">
          <span>Team</span>
          <select value={teamFilter} onChange={(e) => setTeamFilter(e.target.value)}>
            <option value="all">Alle</option>
            {teamOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-chip">
          <span>Priorität</span>
          <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value)}>
            <option value="all">Alle</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
            <option value="critical">critical</option>
          </select>
        </label>
      </div>

      <div className="reports-chart-row">
        <ChartPanel title="Ticketvolumen über Zeit" series={volumeTrend} valueKey="value">
          {volumeTrend.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={volumeTrend} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="vol-fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#5E6AD2" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#5E6AD2" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#F1F2F4" strokeDasharray="3 3" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9AA0AA" }} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9AA0AA" }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="value" stroke="#5E6AD2" strokeWidth={1.5} fill="url(#vol-fill)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Keine Daten im Zeitraum.</p>
          )}
        </ChartPanel>

        <ChartPanel title="Backlog-Entwicklung" series={backlogTrend} valueKey="backlog">
          {backlogTrend.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <LineChart data={backlogTrend} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid vertical={false} stroke="#F1F2F4" strokeDasharray="3 3" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9AA0AA" }} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9AA0AA" }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="created" stroke="#3B82F6" strokeWidth={1.5} dot={false} />
                <Line type="monotone" dataKey="closed" stroke="#30A46C" strokeWidth={1.5} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Keine Backlog-Daten.</p>
          )}
        </ChartPanel>

        <ChartPanel title="Bearbeitungszeit nach Priorität" series={priorityCycle} valueKey="average_hours">
          {priorityCycle.length ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={priorityCycle}
                layout="vertical"
                margin={{ top: 8, right: 8, left: 8, bottom: 0 }}
              >
                <CartesianGrid horizontal={false} stroke="#F1F2F4" strokeDasharray="3 3" />
                <XAxis type="number" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#9AA0AA" }} />
                <YAxis
                  type="category"
                  dataKey="priority"
                  tickLine={false}
                  axisLine={false}
                  width={72}
                  tick={{ fontSize: 11, fill: "#626772" }}
                />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Bar dataKey="average_hours" fill="#5E6AD2" radius={[0, 2, 2, 0]} barSize={12} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="chart-empty">Keine Prozesszeiten.</p>
          )}
        </ChartPanel>
      </div>

      <div className="reports-detail-row">
        <DetailList
          title="Top-Bearbeiter"
          rows={topAssignees.slice(0, 8)}
          formatLabel={(row) => row.name || "—"}
          formatMeta={(row) => `${row.closed_count} geschl. · ${row.active_count} aktiv`}
          emptyLabel="Keine Bearbeitungen im Zeitraum."
        />
        <DetailList
          title="Aktive Teams"
          rows={teamDistribution.slice(0, 8)}
          formatLabel={(row) => row.name || "—"}
          formatMeta={(row) => `${row.value} Tickets`}
          emptyLabel="Noch keine Teamzuordnung."
        />
      </div>
    </div>
  );
}
