import { getOperatorName } from "./userSettings";

export const SAVED_VIEWS_STORAGE_KEY = "ticket-workbench-saved-views";
export const COLUMN_VISIBILITY_STORAGE_KEY = "ticket-workbench-columns";

export const WORKBENCH_VIEWS = {
  all: {
    key: "all",
    label: "Alle Tickets",
    path: "/tickets",
    description: "Gesamter Ticketbestand mit allen Filtern und Sortierungen.",
  },
  mine: {
    key: "mine",
    label: "Meine Tickets",
    path: "/tickets/mine",
    description: "Fälle, die mit deinem Operator-Namen verbunden sind.",
  },
  open: {
    key: "open",
    label: "Offene Tickets",
    path: "/tickets/open",
    description: "Alle noch nicht abgeschlossenen oder final zugewiesenen Vorgänge.",
  },
  escalations: {
    key: "escalations",
    label: "Eskalationen",
    path: "/tickets/escalations",
    description: "Dringende High- und Critical-Fälle mit operativem Fokus.",
  },
};

export const COLUMN_OPTIONS = [
  { key: "ticket_id", label: "Ticket-ID", sortable: true },
  { key: "title", label: "Titel", sortable: true },
  { key: "category", label: "Kategorie", sortable: true },
  { key: "status", label: "Status", sortable: true },
  { key: "priority", label: "Priorität", sortable: true },
  { key: "team", label: "Team", sortable: true },
  { key: "assignee", label: "Bearbeitung", sortable: true },
  { key: "reporter", label: "Ersteller", sortable: true },
  { key: "department", label: "Abteilung", sortable: true },
  { key: "source", label: "Quelle", sortable: true },
  { key: "created_at", label: "Erfasst", sortable: true },
  { key: "updated_at", label: "Letzte Aktivität", sortable: true },
  { key: "due_at", label: "Fällig", sortable: true },
  { key: "tags", label: "Tags", sortable: false },
];

export const DEFAULT_VISIBLE_COLUMNS = [
  "ticket_id",
  "title",
  "category",
  "status",
  "priority",
  "team",
  "reporter",
  "updated_at",
  "tags",
];

export function getCurrentOperator() {
  return getOperatorName();
}

export function loadStoredJson(key, fallback) {
  if (typeof window === "undefined") {
    return fallback;
  }

  try {
    const raw = window.localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

export function persistJson(key, value) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(key, JSON.stringify(value));
}

export function formatSwissDateTime(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "—";
  }

  return new Intl.DateTimeFormat("de-CH", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function getWorkbenchView(viewKey) {
  return WORKBENCH_VIEWS[viewKey] || WORKBENCH_VIEWS.all;
}

export function buildDefaultWorkbenchFilters() {
  return {
    q: "",
    status: "all",
    priority: "all",
    department: "all",
    source: "all",
    sort_by: "updated_at",
    sort_dir: "desc",
    page: 1,
    page_size: 10,
  };
}

export function deriveTicketTags(ticket) {
  if (Array.isArray(ticket.tags) && ticket.tags.length) {
    return ticket.tags;
  }

  const derivedTags = [];

  if (ticket.source) {
    derivedTags.push(ticket.source === "internal" ? "Intern" : ticket.source);
  }

  if (ticket.status === "triaged") {
    derivedTags.push("Prüfung offen");
  }

  if (ticket.priority === "critical") {
    derivedTags.push("Sofort");
  }

  return derivedTags.slice(0, 3);
}
