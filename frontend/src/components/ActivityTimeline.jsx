function formatDateTime(value) {
  if (!value) {
    return "Unbekannte Zeit";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return new Intl.DateTimeFormat("de-CH", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function translateEventType(value) {
  const normalized = String(value || "").toLowerCase();

  return (
    {
      ticket_created: "Ticket erstellt",
      triage_completed: "Triage abgeschlossen",
      review_saved: "Prüfentscheid gespeichert",
      assignment_saved: "Zuweisung gespeichert",
      status_changed: "Status geändert",
      comment_added: "Kommentar",
      internal_note_added: "Interne Notiz",
      ticket_escalated: "Eskaliert",
      unknown: "Unbekannt",
    }[normalized] || value
  );
}

function markerClassName(eventType) {
  const normalized = String(eventType || "").toLowerCase();

  if (normalized === "ticket_escalated") {
    return "activity-timeline-marker is-danger";
  }

  if (normalized === "internal_note_added") {
    return "activity-timeline-marker is-warning";
  }

  if (normalized === "comment_added") {
    return "activity-timeline-marker is-info";
  }

  if (normalized === "status_changed" || normalized === "assignment_saved") {
    return "activity-timeline-marker is-success";
  }

  return "activity-timeline-marker";
}

export default function ActivityTimeline({ events = [] }) {
  if (!events.length) {
    return (
      <div className="detail-empty-state">
        <strong>Kein Verlauf verfügbar</strong>
        <p>Für dieses Ticket sind noch keine Audit-Ereignisse vorhanden.</p>
      </div>
    );
  }

  return (
    <div className="activity-timeline">
      {events.map((event) => (
        <div key={event.id} className="activity-timeline-item">
          <div className={markerClassName(event.eventType)} />
          <div className="activity-timeline-content">
            <div className="activity-timeline-topline">
              <strong>{event.summary}</strong>
              <span>{formatDateTime(event.createdAt)}</span>
            </div>
            <div className="activity-timeline-meta">
              <span>{translateEventType(event.eventType)}</span>
              <span>{event.actor ? `Akteur: ${event.actor}` : "Akteur: System"}</span>
            </div>
            {event.details ? <p>{event.details}</p> : null}
          </div>
        </div>
      ))}
    </div>
  );
}
