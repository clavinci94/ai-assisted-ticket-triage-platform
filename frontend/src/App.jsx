import { BrowserRouter, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import DashboardPage from "./pages/DashboardPage";
import TicketDetailPage from "./pages/TicketDetailPage";
import { ToastProvider } from "./components/ToastProvider";

function AppLayout() {
  return (
    <div>
      <nav className="topnav">
        <div className="topnav-brand">Ticket Triage Platform</div>
        <div className="topnav-links">
          <NavLink to="/" end className="topnav-link">
            Dashboard
          </NavLink>
        </div>
      </nav>

      <Routes>
        <Route path="/" element={<DashboardPage />} />
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
