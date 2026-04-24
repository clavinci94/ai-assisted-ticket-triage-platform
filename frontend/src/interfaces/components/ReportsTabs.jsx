import Tabs from "./Tabs";

const REPORT_VIEWS = [
  { to: "/reports", label: "Übersicht", end: true },
  { to: "/reports/kpis", label: "KPIs" },
  { to: "/reports/departments", label: "Abteilungen" },
  { to: "/reports/teams", label: "Teams" },
  { to: "/reports/sla", label: "SLA / Fristen" },
];

export default function ReportsTabs() {
  return <Tabs items={REPORT_VIEWS} ariaLabel="Reporting-Bereiche" />;
}
