import { Link } from "react-router-dom";
import Badge from "./Badge";

export default function TicketList({
  tickets,
  loading,
  selectedTicketId,
}) {
  if (loading) return <p>Tickets werden geladen...</p>;
  if (!tickets.length) return <p>Keine Tickets gefunden.</p>;

  return (
    <div className="ticket-list">
      {tickets.map((ticket) => (
        <Link
          key={ticket.ticket_id}
          to={`/tickets/${ticket.ticket_id}`}
          className={`ticket-item-link ${selectedTicketId === ticket.ticket_id ? "active" : ""}`}
        >
          <div className={`ticket-item ${selectedTicketId === ticket.ticket_id ? "active" : ""}`}>
            <div className="ticket-item-top">
              <strong>{ticket.title}</strong>
              <Badge value={ticket.status} type="status" />
            </div>
            <span>Reporter: {ticket.reporter || "—"}</span>
            <span>Supportbereich: {ticket.department || "Bank-IT Support"}</span>
            <span>Quelle: {ticket.source}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
