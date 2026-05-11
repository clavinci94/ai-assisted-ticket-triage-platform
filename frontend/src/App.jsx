import { Suspense, lazy, useEffect, useMemo, useState } from "react";
import { BrowserRouter, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import "./App.css";
import {
  ChartIcon,
  GearIcon,
  HomeIcon,
  ListIcon,
  PlusIcon,
  QuestionIcon,
  SearchIcon,
} from "./interfaces/components/Icon";
import { PageHeadingProvider, usePageHeading } from "./interfaces/components/PageHeadingContext";
import { ToastProvider } from "./interfaces/components/ToastProvider";
// Eager imports for the high-traffic top-level pages so the initial paint
// doesn't wait on a second bundle. Detail and analytics pages — bigger
// dependency footprint (Recharts, ticket-detail tabs) — are lazy-loaded
// to keep the entry chunk small.
import DashboardLandingPage from "./interfaces/pages/DashboardLandingPage";
import DashboardPage from "./interfaces/pages/DashboardPage";
import TicketsPage from "./interfaces/pages/TicketsPage";

const DashboardCreatePage = lazy(() => import("./interfaces/pages/DashboardCreatePage"));
const DashboardDepartmentsPage = lazy(() => import("./interfaces/pages/DashboardDepartmentsPage"));
const DashboardKpisPage = lazy(() => import("./interfaces/pages/DashboardKpisPage"));
const ReportsPage = lazy(() => import("./interfaces/pages/ReportsPage"));
const SettingsPage = lazy(() => import("./interfaces/pages/SettingsPage"));
const SlaPage = lazy(() => import("./interfaces/pages/SlaPage"));
const TeamsPage = lazy(() => import("./interfaces/pages/TeamsPage"));
const TicketDetailPage = lazy(() => import("./interfaces/pages/TicketDetailPage"));

import { getOperatorInitials, loadUserSettings } from "./infrastructure/storage/userSettingsStore";

const LAZY_FALLBACK = (
  <div className="lazy-fallback" role="status" aria-live="polite">
    Wird geladen…
  </div>
);

const NAV_ITEMS = [
  { to: "/dashboard", label: "Übersicht", end: true, Icon: HomeIcon },
  { to: "/tickets", label: "Tickets", Icon: ListIcon },
  { to: "/reports", label: "Reports", Icon: ChartIcon },
  { to: "/settings", label: "Einstellungen", end: true, Icon: GearIcon },
];

const FALLBACK_TITLES = [
  { match: (p) => p === "/dashboard", title: "Übersicht" },
  { match: (p) => p === "/dashboard/create", title: "Ticket erfassen" },
  { match: (p) => p.startsWith("/tickets") && !/^\/tickets\/[^/]+$/.test(p), title: "Tickets" },
  { match: (p) => /^\/tickets\/[^/]+$/.test(p), title: "Ticket" },
  { match: (p) => p.startsWith("/reports"), title: "Reports" },
  { match: (p) => p === "/settings", title: "Einstellungen" },
  { match: (p) => p === "/help", title: "Hilfe" },
];

function resolveFallbackTitle(pathname) {
  const hit = FALLBACK_TITLES.find((entry) => entry.match(pathname));
  return hit ? hit.title : "Triage";
}

function AppSidebar() {
  return (
    <aside className="app-sidebar">
      <div className="app-sidebar-brand">Triage</div>

      <nav className="app-sidebar-nav" aria-label="Hauptnavigation">
        {NAV_ITEMS.map((item) => {
          const IconComponent = item.Icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `app-sidebar-link ${isActive ? "active" : ""}`}
            >
              <IconComponent className="app-sidebar-link-icon" width={16} height={16} />
              <span>{item.label}</span>
            </NavLink>
          );
        })}
      </nav>
    </aside>
  );
}

function AppTopbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const { heading } = usePageHeading();
  const [globalSearch, setGlobalSearch] = useState("");
  const [profileLabel, setProfileLabel] = useState("OP");

  const effectiveTitle = heading.title || resolveFallbackTitle(location.pathname);
  const effectiveCount = heading.count;

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    // eslint-disable-next-line react-hooks/set-state-in-effect -- URL → state sync.
    setGlobalSearch(params.get("q") || "");
  }, [location.search]);

  useEffect(() => {
    const syncSettings = () => {
      loadUserSettings();
      setProfileLabel(getOperatorInitials());
    };
    syncSettings();
    window.addEventListener("ticket-triage-settings-updated", syncSettings);
    return () => {
      window.removeEventListener("ticket-triage-settings-updated", syncSettings);
    };
  }, [location.pathname]);

  useEffect(() => {
    const handler = (event) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        const input = document.querySelector('[data-global-search] input');
        input?.focus();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleSearchSubmit = (event) => {
    event.preventDefault();
    const params = new URLSearchParams();
    if (globalSearch.trim()) params.set("q", globalSearch.trim());
    navigate(`/tickets?${params.toString()}`);
  };

  return (
    <header className="app-topbar">
      <div className="app-topbar-title">
        <strong>{effectiveTitle}</strong>
        {effectiveCount != null ? <span className="app-topbar-count tabular-nums">{effectiveCount}</span> : null}
      </div>

      <form className="app-topbar-search" data-global-search onSubmit={handleSearchSubmit}>
        <SearchIcon className="app-topbar-search-icon" width={14} height={14} />
        <input
          type="search"
          placeholder="Tickets, IDs oder Reporter durchsuchen"
          value={globalSearch}
          onChange={(event) => setGlobalSearch(event.target.value)}
        />
        <kbd className="app-topbar-kbd">⌘K</kbd>
      </form>

      <div className="app-topbar-actions">
        <button
          type="button"
          className="app-topbar-icon-button"
          onClick={() => navigate("/help")}
          title="Hilfe & Plattform-Einstieg"
          aria-label="Hilfe"
        >
          <QuestionIcon width={16} height={16} />
        </button>

        <button
          type="button"
          className="app-topbar-profile"
          onClick={() => navigate("/settings")}
          title="Einstellungen"
        >
          {profileLabel}
        </button>

        <button
          type="button"
          className="app-topbar-primary"
          onClick={() => navigate("/dashboard/create")}
        >
          <PlusIcon width={14} height={14} />
          <span>Neues Ticket</span>
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
          <Suspense fallback={LAZY_FALLBACK}>
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/dashboard/create" element={<DashboardCreatePage />} />
              <Route path="/tickets" element={<TicketsPage initialView="all" />} />
              <Route path="/tickets/mine" element={<TicketsPage initialView="mine" />} />
              <Route path="/tickets/open" element={<TicketsPage initialView="open" />} />
              <Route path="/tickets/escalations" element={<TicketsPage initialView="escalations" />} />
              <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
              <Route path="/reports" element={<ReportsPage />} />
              <Route path="/reports/kpis" element={<DashboardKpisPage />} />
              <Route path="/reports/departments" element={<DashboardDepartmentsPage />} />
              <Route path="/reports/teams" element={<TeamsPage />} />
              <Route path="/reports/sla" element={<SlaPage />} />
              <Route path="/settings" element={<SettingsPage />} />
              <Route path="/help" element={<DashboardLandingPage />} />
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Suspense>
        </main>
      </div>
    </div>
  );
}

// Hush: heading read in AppTopbar but consumer also sets, so put
// provider OUTSIDE routes so every screen can push heading updates.
function AppShell() {
  // Placeholder kept for future provider composition — context stays
  // above AppLayout so both sidebar and topbar consume the same heading.
  useMemo(() => null, []); // no-op to keep linter quiet while structure is stable
  return <AppLayout />;
}

export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <PageHeadingProvider>
          <AppShell />
        </PageHeadingProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
