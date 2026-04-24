import { useEffect, useMemo, useState } from "react";
import { BrowserRouter, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import "./App.css";
import { ToastProvider } from "./interfaces/components/ToastProvider";
import DashboardCreatePage from "./interfaces/pages/DashboardCreatePage";
import DashboardDepartmentsPage from "./interfaces/pages/DashboardDepartmentsPage";
import DashboardKpisPage from "./interfaces/pages/DashboardKpisPage";
import DashboardLandingPage from "./interfaces/pages/DashboardLandingPage";
import DashboardPage from "./interfaces/pages/DashboardPage";
import ReportsPage from "./interfaces/pages/ReportsPage";
import SettingsPage from "./interfaces/pages/SettingsPage";
import SlaPage from "./interfaces/pages/SlaPage";
import TeamsPage from "./interfaces/pages/TeamsPage";
import TicketDetailPage from "./interfaces/pages/TicketDetailPage";
import TicketsPage from "./interfaces/pages/TicketsPage";
import { getOperatorInitials, loadUserSettings } from "./infrastructure/storage/userSettingsStore";

const NAV_SECTIONS = [
  {
    label: "Einführung",
    items: [
      { to: "/", label: "Startseite", end: true },
    ],
  },
  {
    label: "Arbeitsbereich",
    items: [
      { to: "/dashboard", label: "Übersicht" },
      { to: "/tickets", label: "Alle Tickets", end: true },
      { to: "/tickets/mine", label: "Meine Tickets", end: true },
      { to: "/tickets/open", label: "Offene Tickets", end: true },
      { to: "/tickets/escalations", label: "Eskalationen", end: true },
      { to: "/dashboard/create", label: "Ticket erfassen" },
    ],
  },
  {
    label: "Reporting & Governance",
    items: [
      { to: "/reports", label: "Reports", end: true },
      { to: "/reports/kpis", label: "KPIs" },
      { to: "/reports/departments", label: "Abteilungen" },
      { to: "/reports/teams", label: "Teams" },
      { to: "/reports/sla", label: "SLA / Fristen" },
      { to: "/settings", label: "Einstellungen" },
    ],
  },
];

const ROUTE_META = [
  {
    match: (pathname) => pathname === "/",
    title: "Plattform-Einstieg",
    subtitle: "Verstehe Aufbau, Bedienung und die Rolle der einzelnen Bereiche.",
  },
  {
    match: (pathname) => pathname === "/dashboard",
    title: "Operative Arbeitszentrale",
    subtitle: "Überblick, Warteschlange und Handlungsbedarf in einem fokussierten Arbeitsbereich.",
  },
  {
    match: (pathname) => pathname === "/tickets",
    title: "Alle Tickets",
    subtitle: "Zentrale Workbench für Suche, Filter, Bulk-Aktionen und Tabellenarbeit.",
  },
  {
    match: (pathname) => pathname === "/tickets/mine",
    title: "Meine Tickets",
    subtitle: "Persönliche Sicht auf Vorgänge, die deinem Operator-Namen zugeordnet sind.",
  },
  {
    match: (pathname) => pathname === "/tickets/open",
    title: "Offene Tickets",
    subtitle: "Alle noch offenen Tickets in einer fokussierten Bearbeitungsansicht.",
  },
  {
    match: (pathname) => pathname === "/tickets/escalations",
    title: "Eskalationen",
    subtitle: "High- und Critical-Fälle mit unmittelbarem Handlungsbedarf.",
  },
  {
    match: (pathname) => pathname === "/dashboard/create",
    title: "Ticket-Erfassung",
    subtitle: "Neue Fälle aufnehmen und mit KI-Empfehlung für die Abteilung anlegen.",
  },
  {
    match: (pathname) => pathname === "/reports",
    title: "Reports Übersicht",
    subtitle: "Volumen, Backlog, SLA und Ownership in einem gemeinsamen Reporting-Hub.",
  },
  {
    match: (pathname) => pathname === "/dashboard/kpis" || pathname === "/reports/kpis",
    title: "KPI-Ansicht",
    subtitle: "Status, Prioritäten und Prozesskennzahlen für das operative Reporting.",
  },
  {
    match: (pathname) => pathname === "/dashboard/departments" || pathname === "/reports/departments",
    title: "Abteilungsanalyse",
    subtitle: "Verteilung, Auslastung und Ownership nach Fachbereich im Blick behalten.",
  },
  {
    match: (pathname) => pathname === "/reports/teams",
    title: "Teamreport",
    subtitle: "Teamlast, Ownership und Bearbeitungsfokus pro Squad oder Service Desk.",
  },
  {
    match: (pathname) => pathname === "/reports/sla",
    title: "SLA & Fristen",
    subtitle: "Fristverletzungen, Due-Soon-Fälle und SLA-Risiken operativ steuern.",
  },
  {
    match: (pathname) => pathname === "/settings",
    title: "Einstellungen",
    subtitle: "Lokale Präferenzen für Operator, Dashboard-Einstieg und Reporting-Navigation.",
  },
  {
    match: (pathname) => pathname.startsWith("/tickets/"),
    title: "Ticket-Detailansicht",
    subtitle: "Prüfen, zuweisen und den Audit-Trail direkt am einzelnen Vorgang steuern.",
  },
];

function AppSidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-brand">
        <span className="app-sidebar-brand-label">Enterprise Support</span>
        <strong>Ticket-Triage-Plattform</strong>
        <p>Interne Arbeitsoberfläche für Triage, Prüfung und Routing.</p>
      </div>

      <nav className="app-sidebar-nav" aria-label="Hauptnavigation">
        {NAV_SECTIONS.map((section) => (
          <div key={section.label} className="app-sidebar-group">
            <span className="app-sidebar-group-label">{section.label}</span>
            <div className="app-sidebar-links">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) => `app-sidebar-link ${isActive ? "active" : ""}`}
                >
                  {item.label}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="app-sidebar-card">
        <span className="app-sidebar-card-label">Arbeitsmodus</span>
        <strong>Operativer Fokus</strong>
        <p>Dashboard, Prüfung und Routing sind auf schnelle Entscheidungen im Tagesgeschäft ausgerichtet.</p>
      </div>
    </aside>
  );
}

function AppTopbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [globalSearch, setGlobalSearch] = useState("");
  const [profileLabel, setProfileLabel] = useState("OP");
  const [reportsStartPage, setReportsStartPage] = useState("/reports");

  const routeMeta = useMemo(
    () =>
      ROUTE_META.find((entry) => entry.match(location.pathname)) || {
        title: "Ticket-Triage-Plattform",
        subtitle: "Arbeite fokussiert über Dashboard, Detailansichten und Analysebereiche.",
      },
    [location.pathname]
  );

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing URL → state is exactly the kind of external-sync effect allowed by the rule.
    setGlobalSearch(params.get("q") || "");
  }, [location.search]);

  useEffect(() => {
    const syncSettings = () => {
      const settings = loadUserSettings();
      setProfileLabel(getOperatorInitials());
      setReportsStartPage(settings.reportsStartPage || "/reports");
    };

    syncSettings();
    window.addEventListener("ticket-triage-settings-updated", syncSettings);

    return () => {
      window.removeEventListener("ticket-triage-settings-updated", syncSettings);
    };
  }, [location.pathname]);

  const handleSearchSubmit = (event) => {
    event.preventDefault();

    const params = new URLSearchParams();

    if (globalSearch.trim()) {
      params.set("q", globalSearch.trim());
    }

    navigate(`/tickets?${params.toString()}`);
  };

  return (
    <header className="app-topbar">
      <div className="app-topbar-copy">
        <span className="app-topbar-eyebrow">Ticket Operations</span>
        <strong>{routeMeta.title}</strong>
        <p>{routeMeta.subtitle}</p>
      </div>

      <div className="app-topbar-actions">
        <form className="app-topbar-search" onSubmit={handleSearchSubmit}>
          <input
            type="search"
            placeholder="Tickets, IDs oder Reporter durchsuchen"
            value={globalSearch}
            onChange={(event) => setGlobalSearch(event.target.value)}
          />
          <button type="submit">Suchen</button>
        </form>

        <button type="button" className="app-topbar-action app-topbar-action-primary" onClick={() => navigate("/dashboard/create")}>
          Neues Ticket
        </button>

        <button type="button" className="app-topbar-action" onClick={() => navigate("/")}>
          Hinweise
          <span className="app-topbar-pill">3</span>
        </button>

        <button type="button" className="app-topbar-action" onClick={() => navigate(reportsStartPage)}>
          Reports
        </button>

        <button
          type="button"
          className="app-topbar-profile"
          onClick={() => navigate("/settings")}
          title="Zu den Einstellungen"
        >
          {profileLabel}
        </button>
      </div>
    </header>
  );
}

function AppLayout() {
  return (
    <div className="app-frame">
      <AppSidebar />

      <div className="app-main">
        <AppTopbar />

        <main className="app-content">
          <Routes>
            <Route path="/" element={<DashboardLandingPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/dashboard/departments" element={<DashboardDepartmentsPage />} />
            <Route path="/dashboard/create" element={<DashboardCreatePage />} />
            <Route path="/dashboard/kpis" element={<DashboardKpisPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/reports/kpis" element={<DashboardKpisPage />} />
            <Route path="/reports/departments" element={<DashboardDepartmentsPage />} />
            <Route path="/reports/teams" element={<TeamsPage />} />
            <Route path="/reports/sla" element={<SlaPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/tickets" element={<TicketsPage initialView="all" />} />
            <Route path="/tickets/mine" element={<TicketsPage initialView="mine" />} />
            <Route path="/tickets/open" element={<TicketsPage initialView="open" />} />
            <Route path="/tickets/escalations" element={<TicketsPage initialView="escalations" />} />
            <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppLayout />
      </ToastProvider>
    </BrowserRouter>
  );
}
