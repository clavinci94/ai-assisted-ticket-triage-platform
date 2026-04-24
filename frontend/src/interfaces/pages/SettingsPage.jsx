import { useMemo, useState } from "react";
import { useSetPageHeading } from "../components/PageHeadingContext";
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
  const { showToast } = useToast();
  const initialSettings = useMemo(() => loadUserSettings(), []);
  const [settings, setSettings] = useState(initialSettings);

  useSetPageHeading("Einstellungen");

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
    <div className="app-shell settings-shell">
      <form className="settings-form" onSubmit={handleSubmit}>
        <div className="settings-field">
          <label htmlFor="settings-operator">Operator-Name</label>
          <p className="settings-helper">Wird in Workbench, Kommentaren und Statuswechseln als Akteur verwendet.</p>
          <input
            id="settings-operator"
            type="text"
            value={settings.operatorName}
            onChange={(event) => handleChange("operatorName", event.target.value)}
            placeholder="z. B. Claudio"
          />
        </div>

        <div className="settings-field">
          <label htmlFor="settings-workspace">Dashboard-Startbereich</label>
          <p className="settings-helper">Bestimmt die Standard-Ansicht, wenn du das Dashboard ohne Parameter öffnest.</p>
          <select
            id="settings-workspace"
            value={settings.dashboardWorkspace}
            onChange={(event) => handleChange("dashboardWorkspace", event.target.value)}
          >
            {DASHBOARD_WORKSPACES.map((workspace) => (
              <option key={workspace.value} value={workspace.value}>
                {workspace.label}
              </option>
            ))}
          </select>
        </div>

        <div className="settings-field">
          <label htmlFor="settings-reports">Standardseite für Reports</label>
          <p className="settings-helper">Welcher Reporting-Tab beim Öffnen von Reports vorausgewählt wird.</p>
          <select
            id="settings-reports"
            value={settings.reportsStartPage}
            onChange={(event) => handleChange("reportsStartPage", event.target.value)}
          >
            {REPORT_START_PAGES.map((page) => (
              <option key={page.value} value={page.value}>
                {page.label}
              </option>
            ))}
          </select>
        </div>

        <div className="settings-actions">
          <button type="submit" className="primary-button">Einstellungen speichern</button>
        </div>
      </form>
    </div>
  );
}
