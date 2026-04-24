import { Link } from "react-router-dom";
import Badge from "./Badge";
import { COLUMN_OPTIONS, deriveTicketTags, formatSwissDateTime } from "../../application/tickets/ticketWorkbench";

function normalizeValue(value) {
  return String(value || "").trim().toLowerCase();
}

function shortId(id) {
  if (!id) return "—";
  const value = String(id);
  return value.length > 8 ? `${value.slice(0, 8)}…` : value;
}

function relativeTime(timestamp) {
  if (!timestamp) return "—";
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return "—";
  const diff = Math.max(0, Date.now() - date.getTime());
  const min = Math.floor(diff / 60_000);
  if (min < 1) return "jetzt";
  if (min < 60) return `vor ${min} Min`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `vor ${hr} Std`;
  const d = Math.floor(hr / 24);
  if (d < 7) return `vor ${d} Tg`;
  const w = Math.floor(d / 7);
  if (w < 5) return `vor ${w} Wo`;
  return date.toLocaleDateString("de-DE", { day: "2-digit", month: "2-digit", year: "2-digit" });
}

function StatusPill({ value }) {
  const v = normalizeValue(value);
  let cls = "pill-open";
  if (v === "triaged" || v === "in_review") cls = "pill-triaged";
  else if (v === "review" || v === "in_progress") cls = "pill-review";
  else if (v === "resolved") cls = "pill-resolved";
  else if (v === "closed") cls = "pill-closed";
  return <span className={`pill ${cls}`}>{value || "—"}</span>;
}

function CategoryPill({ value }) {
  const v = normalizeValue(value);
  const known = ["bug", "feature", "support", "requirement", "question"];
  const key = known.includes(v) ? v : "unknown";
  return <span className={`pill pill-cat-${key}`}>{value || "—"}</span>;
}

function PriorityCell({ value }) {
  const v = normalizeValue(value);
  const tone =
    v === "critical" ? "prio-critical" : v === "high" ? "prio-high" : v === "low" ? "prio-low" : "prio-medium";
  return (
    <span className={`prio-dot ${tone}`}>
      <span>{value || "medium"}</span>
    </span>
  );
}

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
    return (
      <span className="cell-id mono" title={ticket.ticket_id}>
        {shortId(ticket.ticket_id)}
      </span>
    );
  }

  if (columnKey === "title") {
    return (
      <Link className="cell-title" to={`/tickets/${ticket.ticket_id}`}>
        {ticket.title}
      </Link>
    );
  }

  if (columnKey === "category") {
    return <CategoryPill value={ticket.category} />;
  }

  if (columnKey === "status") {
    return <StatusPill value={ticket.status} />;
  }

  if (columnKey === "priority") {
    return <PriorityCell value={ticket.priority} />;
  }

  if (columnKey === "team") {
    return <span className="cell-muted">{ticket.team || "—"}</span>;
  }

  if (columnKey === "assignee") {
    return <span className="cell-muted">{ticket.assignee || "—"}</span>;
  }

  if (columnKey === "reporter") {
    return <span className="cell-muted">{ticket.reporter || "—"}</span>;
  }

  if (columnKey === "department") {
    return <span className="cell-muted">{ticket.department || "—"}</span>;
  }

  if (columnKey === "source") {
    return <span className="cell-muted">{ticket.source || "—"}</span>;
  }

  if (columnKey === "updated_at" || columnKey === "created_at" || columnKey === "activity") {
    const ts = ticket.updated_at || ticket.created_at;
    return (
      <span className="cell-time tabular-nums" title={formatSwissDateTime(ts)}>
        {relativeTime(ts)}
      </span>
    );
  }

  if (columnKey === "due_at") {
    if (!ticket.due_at) return <span className="cell-muted">—</span>;
    return (
      <span className="cell-time tabular-nums" title={formatSwissDateTime(ticket.due_at)}>
        {relativeTime(ticket.due_at)}
      </span>
    );
  }

  if (columnKey === "tags") {
    const tags = deriveTicketTags(ticket);
    if (!tags.length) return <span className="cell-muted">—</span>;
    const visible = tags.slice(0, 2);
    const overflow = tags.length - visible.length;
    return (
      <div className="cell-tags">
        {visible.map((tag) => (
          <span key={`${ticket.ticket_id}-${tag}`} className="cell-tag">
            {tag}
          </span>
        ))}
        {overflow > 0 ? <span className="cell-tag cell-tag-overflow">+{overflow}</span> : null}
      </div>
    );
  }

  return <span className="cell-muted">{ticket[columnKey] || "—"}</span>;
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
