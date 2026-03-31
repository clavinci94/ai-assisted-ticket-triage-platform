import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider";
import { DEFAULT_USER_SETTINGS, loadUserSettings, saveUserSettings } from "../../infrastructure/storage/userSettingsStore";

const DASHBOARD_WORKSPACES = [
  { value: "overview", label: "Übersicht" },
  { value: "tickets", label: "Ticket-Warteschlange" },
  { value: "operations", label: "Nächste Schritte" },
];

const REPORT_START_PAGES = [
  { value: "/reports", label: "Reports Übersicht" },
  { value: "/reports/kpis", label: "KPI-Report" },
  { value: "/reports/departments", label: "Abteilungsreport" },
  { value: "/reports/teams", label: "Teamreport" },
  { value: "/reports/sla", label: "SLA-Report" },
];

export default function SettingsPage() {
  const navigate = useNavigate();
  const { showToast } = useToast();
  const initialSettings = useMemo(() => loadUserSettings(), []);
  const [settings, setSettings] = useState(initialSettings);

  function handleChange(key, value) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();

    const saved = saveUserSettings({
      operatorName: settings.operatorName.trim() || DEFAULT_USER_SETTINGS.operatorName,
      dashboardWorkspace: settings.dashboardWorkspace,
      reportsStartPage: settings.reportsStartPage,
    });

    setSettings(saved);
    showToast({
      type: "success",
      title: "Einstellungen gespeichert",
      message: "Operator- und Navigationspräferenzen wurden lokal übernommen.",
    });
  }

  return (
    <div className="app-shell dashboard-shell">
      <header className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Governance</p>
          <h1>Einstellungen</h1>
          <p className="subtitle">
            Lokale Präferenzen für Operator-Namen und Standardnavigation im Dashboard.
          </p>
        </div>
      </header>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Governance</span>
          <span>•</span>
          <span>Einstellungen</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button type="button" onClick={() => navigate("/reports")}>Reports</button>
        </div>
      </section>

      <section className="settings-grid">
        <form className="settings-panel" onSubmit={handleSubmit}>
          <div className="settings-panel-header">
            <span className="chart-card-eyebrow">Operator</span>
            <h3>Arbeitsprofil</h3>
            <p>Diese Werte beeinflussen Workbench, Detailansicht und Standardnavigation.</p>
          </div>

          <div className="settings-form-grid">
            <label className="detail-form-field">
              <span>Operator-Name</span>
              <input
                type="text"
                value={settings.operatorName}
                onChange={(event) => handleChange("operatorName", event.target.value)}
                placeholder="z. B. Claudio"
              />
            </label>

            <label className="detail-form-field">
              <span>Dashboard-Startbereich</span>
              <select
                value={settings.dashboardWorkspace}
                onChange={(event) => handleChange("dashboardWorkspace", event.target.value)}
              >
                {DASHBOARD_WORKSPACES.map((workspace) => (
                  <option key={workspace.value} value={workspace.value}>
                    {workspace.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="detail-form-field">
              <span>Standardseite für Reports</span>
              <select
                value={settings.reportsStartPage}
                onChange={(event) => handleChange("reportsStartPage", event.target.value)}
              >
                {REPORT_START_PAGES.map((page) => (
                  <option key={page.value} value={page.value}>
                    {page.label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="detail-action-row">
            <button className="primary-button" type="submit">Einstellungen speichern</button>
          </div>
        </form>

        <div className="settings-panel">
          <div className="settings-panel-header">
            <span className="chart-card-eyebrow">Wirkung</span>
            <h3>Wo die Einstellungen greifen</h3>
          </div>
          <div className="settings-note-list">
            <div className="settings-note-item">
              <strong>Operator-Name</strong>
              <p>Wird in Workbench, Ticket-Detailansicht, Kommentaren und Statuswechseln verwendet.</p>
            </div>
            <div className="settings-note-item">
              <strong>Dashboard-Startbereich</strong>
              <p>Wird genutzt, wenn du das Dashboard ohne expliziten Workspace öffnest.</p>
            </div>
            <div className="settings-note-item">
              <strong>Reports-Startseite</strong>
              <p>Bestimmt, welcher Reporting-Bereich als Standard-Einstieg dient.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
