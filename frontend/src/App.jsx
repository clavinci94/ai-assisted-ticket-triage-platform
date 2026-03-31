import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import DashboardLandingPage from "./pages/DashboardLandingPage";
import DashboardPage from "./pages/DashboardPage";
import DashboardCreatePage from "./pages/DashboardCreatePage";
import DashboardDepartmentsPage from "./pages/DashboardDepartmentsPage";
import DashboardKpisPage from "./pages/DashboardKpisPage";
import TicketDetailPage from "./pages/TicketDetailPage";
import { ToastProvider } from "./components/ToastProvider";

function AppLayout() {
  return (
    <div>
      <nav className="topnav">
        <div className="topnav-brand">Ticket-Triage-Plattform</div>
        <div className="topnav-links">
          <NavLink to="/" end className="topnav-link">
            Startseite
          </NavLink>
          <NavLink to="/dashboard" className="topnav-link">
            Dashboard-Übersicht
          </NavLink>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<DashboardLandingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard/departments" element={<DashboardDepartmentsPage />} />
        <Route path="/dashboard/create" element={<DashboardCreatePage />} />
        <Route path="/dashboard/kpis" element={<DashboardKpisPage />} />
        <Route path="/tickets/:ticketId" element={<TicketDetailPage />} />
      </Routes>
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
