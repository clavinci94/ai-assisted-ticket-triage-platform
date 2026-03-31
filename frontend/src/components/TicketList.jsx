import { Link } from "react-router-dom";
import Badge from "./Badge";
import { COLUMN_OPTIONS, deriveTicketTags, formatSwissDateTime } from "../lib/ticketWorkbench";

function CompactTicketList({ tickets, loading, selectedTicketId }) {
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

function SortButton({ column, activeSortBy, activeSortDir, onSort }) {
  const isActive = activeSortBy === column.key;

  return (
    <button
      type="button"
      className={`ticket-table-sort ${isActive ? "active" : ""}`}
      onClick={() => onSort(column.key)}
      disabled={column.sortable === false}
    >
      <span>{column.label}</span>
      {column.sortable === false ? null : (
        <strong>{isActive ? (activeSortDir === "asc" ? "↑" : "↓") : "↕"}</strong>
      )}
    </button>
  );
}

function renderCell(ticket, columnKey) {
  if (columnKey === "ticket_id") {
    return <span className="ticket-table-mono">{ticket.ticket_id}</span>;
  }

  if (columnKey === "title") {
    return (
      <div className="ticket-table-title">
        <Link to={`/tickets/${ticket.ticket_id}`}>{ticket.title}</Link>
        <span>{ticket.description || "Keine Beschreibung verfügbar."}</span>
      </div>
    );
  }

  if (columnKey === "category") {
    return <Badge value={ticket.category} type="category" />;
  }

  if (columnKey === "status") {
    return <Badge value={ticket.status} type="status" />;
  }

  if (columnKey === "priority") {
    return <Badge value={ticket.priority} type="priority" />;
  }

  if (columnKey === "team") {
    return ticket.team || "Noch offen";
  }

  if (columnKey === "assignee") {
    return ticket.assignee || "Nicht hinterlegt";
  }

  if (columnKey === "reporter") {
    return ticket.reporter || "—";
  }

  if (columnKey === "department") {
    return ticket.department || "—";
  }

  if (columnKey === "source") {
    return ticket.source || "—";
  }

  if (columnKey === "created_at") {
    return formatSwissDateTime(ticket.created_at);
  }

  if (columnKey === "updated_at") {
    return formatSwissDateTime(ticket.updated_at);
  }

  if (columnKey === "due_at") {
    return ticket.due_at ? formatSwissDateTime(ticket.due_at) : "Noch nicht definiert";
  }

  if (columnKey === "tags") {
    const tags = deriveTicketTags(ticket);

    if (!tags.length) {
      return "—";
    }

    return (
      <div className="ticket-tag-row">
        {tags.map((tag) => (
          <span key={`${ticket.ticket_id}-${tag}`} className="ticket-tag">
            {tag}
          </span>
        ))}
      </div>
    );
  }

  return ticket[columnKey] || "—";
}

function TableTicketList({
  tickets,
  loading,
  visibleColumns = [],
  selectedTicketIds = [],
  onToggleSelect,
  onToggleSelectAll,
  onSort,
  sortBy,
  sortDir,
}) {
  const columns = COLUMN_OPTIONS.filter((column) => visibleColumns.includes(column.key));
  const allSelected = tickets.length > 0 && tickets.every((ticket) => selectedTicketIds.includes(ticket.ticket_id));

  if (loading) {
    return <p>Ticket-Workbench wird geladen...</p>;
  }

  if (!tickets.length) {
    return <p>Keine Tickets passend zur aktuellen Sicht gefunden.</p>;
  }

  return (
    <div className="ticket-table-shell">
      <table className="ticket-table">
        <thead>
          <tr>
            <th className="ticket-table-select-column">
              <input
                type="checkbox"
                checked={allSelected}
                onChange={() => onToggleSelectAll(tickets)}
                aria-label="Aktuelle Seite auswählen"
              />
            </th>
            {columns.map((column) => (
              <th key={column.key}>
                <SortButton column={column} activeSortBy={sortBy} activeSortDir={sortDir} onSort={onSort} />
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {tickets.map((ticket) => {
            const selected = selectedTicketIds.includes(ticket.ticket_id);

            return (
              <tr key={ticket.ticket_id} className={selected ? "selected" : ""}>
                <td className="ticket-table-select-column">
                  <input
                    type="checkbox"
                    checked={selected}
                    onChange={() => onToggleSelect(ticket.ticket_id)}
                    aria-label={`Ticket ${ticket.ticket_id} auswählen`}
                  />
                </td>
                {columns.map((column) => (
                  <td key={`${ticket.ticket_id}-${column.key}`}>
                    {renderCell(ticket, column.key)}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default function TicketList(props) {
  if (props.variant === "table") {
    return <TableTicketList {...props} />;
  }

  return <CompactTicketList {...props} />;
}
