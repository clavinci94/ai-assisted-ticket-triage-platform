import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as ToastModule from "../components/ToastProvider";
import Badge from "../components/Badge";
import MessageBanner from "../components/MessageBanner";
import SectionCard from "../components/SectionCard";
import { api } from "../lib/api";

const TABS = [
  { key: "overview", label: "Übersicht" },
  { key: "review", label: "Prüfung" },
  { key: "assignment", label: "Zuweisung" },
];

function readErrorMessage(error) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    "Ein unerwarteter Fehler ist aufgetreten."
  );
}

function pickFirst(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return value;
    }
  }
  return null;
}

function formatConfidence(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "—";
  }
  const numeric = Number(value);
  if (numeric > 0 && numeric <= 1) {
    return `${Math.round(numeric * 100)}%`;
  }
  return `${Math.round(numeric)}%`;
}

function formatLabel(value, fallback = "Nicht verfügbar") {
  return pickFirst(value) ?? fallback;
}

function formatDateTime(value) {
  if (!value) {
    return "Unbekannte Zeit";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}

function normalizeEvent(event, index) {
  if (!event || typeof event !== "object") {
    return {
      id: `event-${index}`,
      eventType: "unknown",
      actor: null,
      summary: "Unbekanntes Ereignis",
      details: null,
      createdAt: null,
    };
  }

  return {
    id: pickFirst(event.id, `event-${index}`),
    eventType: pickFirst(event.event_type, event.eventType, "unknown"),
    actor: pickFirst(event.actor),
    summary: pickFirst(event.summary, "Ereignis erfasst"),
    details: pickFirst(event.details),
    createdAt: pickFirst(event.created_at, event.createdAt),
  };
}

function formatCategory(value) {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      bug: "Fehler",
      feature: "Funktion",
      support: "Support",
      requirement: "Anforderung",
      question: "Frage",
      unknown: "Unbekannt",
    }[normalized] || formatLabel(value)
  );
}

function formatPriority(value) {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      low: "Niedrig",
      medium: "Mittel",
      high: "Hoch",
      critical: "Kritisch",
      unknown: "Unbekannt",
    }[normalized] || formatLabel(value)
  );
}

function formatStatus(value) {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      new: "Neu",
      triaged: "Triagiert",
      reviewed: "Geprüft",
      assigned: "Zugewiesen",
      open: "Offen",
    }[normalized] || formatLabel(value)
  );
}

function formatReviewDecision(value) {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      accepted: "Akzeptiert",
      rejected: "Abgelehnt",
      needs_review: "Weitere Prüfung nötig",
      escalated: "Eskaliert",
      pending: "Ausstehend",
    }[normalized] || formatLabel(value)
  );
}

function formatEventType(value) {
  const normalized = String(value || "").toLowerCase();
  return (
    {
      ticket_created: "Ticket erstellt",
      triage_completed: "Triage abgeschlossen",
      review_saved: "Prüfentscheid gespeichert",
      assignment_saved: "Zuweisung gespeichert",
      status_changed: "Status geändert",
      unknown: "Unbekannt",
    }[normalized] || formatLabel(value)
  );
}

function normalizeTicket(ticket) {
  if (!ticket || typeof ticket !== "object") {
    return null;
  }

  const finalCategory = pickFirst(
    ticket.final_category,
    ticket.category,
    ticket.predicted_category,
    ticket.ai_category,
    ticket.decision?.final_category,
    ticket.analysis?.predicted_category,
    ticket.ai_prediction?.category
  );
  const department = pickFirst(
    ticket.department,
    ticket.analysis?.suggested_department,
    ticket.department_name,
    ticket.area,
    "Bank-IT Support"
  );

  const finalPriority = pickFirst(
    ticket.final_priority,
    ticket.priority,
    ticket.predicted_priority,
    ticket.ai_priority,
    ticket.decision?.final_priority,
    ticket.analysis?.predicted_priority,
    ticket.ai_prediction?.priority
  );

  const assignee = pickFirst(
    ticket.assigned_to,
    ticket.assignee,
    ticket.owner,
    ticket.final_assignee,
    ticket.assignment?.assigned_team
  );

  const confidence = pickFirst(
    ticket.confidence,
    ticket.ai_confidence,
    ticket.prediction_confidence,
    ticket.analysis?.category_confidence,
    ticket.ai_prediction?.confidence
  );

  const summary = pickFirst(
    ticket.summary,
    ticket.ai_summary,
    ticket.generated_summary,
    ticket.analysis?.summary
  );

  const description = pickFirst(
    ticket.description,
    ticket.body,
    ticket.text,
    ticket.content
  );

  const rationale = pickFirst(
    ticket.rationale,
    ticket.analysis?.rationale,
    ticket.analysis?.explanation,
    ticket.ai_rationale
  );

  const nextStep = pickFirst(
    ticket.next_step,
    ticket.analysis?.next_step,
    ticket.ai_next_step
  );

  const suggestedTeam = pickFirst(
    ticket.suggested_team,
    ticket.analysis?.suggested_team,
    ticket.ai_team
  );

  const title = pickFirst(
    ticket.title,
    ticket.subject,
    summary,
    `Ticket #${pickFirst(ticket.id, ticket.ticket_id, ticket.ticketId, "Unknown")}`
  );

  const status = pickFirst(
    ticket.status,
    ticket.state,
    ticket.workflow_status,
    "open"
  );

  const createdAt = pickFirst(
    ticket.created_at,
    ticket.createdAt,
    ticket.timestamp
  );

  const updatedAt = pickFirst(
    ticket.updated_at,
    ticket.updatedAt,
    createdAt
  );

  const reviewDecision = pickFirst(
    ticket.review_decision,
    ticket.final_decision,
    ticket.decision?.final_category ? `${ticket.decision.final_category} / ${ticket.decision.final_priority}` : null
  );

  const reviewReason = pickFirst(
    ticket.review_reason,
    ticket.reason,
    ticket.notes,
    ticket.decision?.review_comment
  );

  const events = Array.isArray(ticket.events)
    ? ticket.events.map(normalizeEvent)
    : [];

  return {
    raw: ticket,
    id: pickFirst(ticket.id, ticket.ticket_id, ticket.ticketId, "Unknown"),
    title,
    description,
    summary,
    category: finalCategory,
    priority: finalPriority,
    department,
    rationale,
    nextStep,
    suggestedTeam,
    assignee,
    confidence,
    status,
    createdAt,
    updatedAt,
    reviewDecision,
    reviewReason,
    events,
  };
}

function InfoStat({ label, value }) {
  return (
    <div className="detail-stat">
      <span className="detail-stat-label">{label}</span>
      <span className="detail-stat-value">{value}</span>
    </div>
  );
}

function EmptyInline({ title, text }) {
  return (
    <div className="detail-empty-state">
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  );
}

function EventItem({ event }) {
  return (
    <div className="detail-event-item">
      <div className="detail-event-marker" />
      <div className="detail-event-content">
        <div className="detail-event-topline">
          <strong>{event.summary}</strong>
          <span>{formatDateTime(event.createdAt)}</span>
        </div>
        <div className="detail-event-meta">
          <span className="detail-event-type">{formatEventType(event.eventType)}</span>
          <span>{event.actor ? `Akteur: ${event.actor}` : "Akteur: System"}</span>
        </div>
        {event.details ? <p>{event.details}</p> : null}
      </div>
    </div>
  );
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const toastApi = ToastModule.useToast?.() ?? null;

  const emitToast = useCallback(
    ({ type = "info", title, description }) => {
      if (toastApi?.toast) {
        toastApi.toast({
          title,
          description,
          variant: type === "error" ? "destructive" : "default",
        });
        return;
      }

      if (toastApi?.addToast) {
        toastApi.addToast({
          type,
          title,
          message: description,
        });
        return;
      }

      if (toastApi?.showToast) {
        toastApi.showToast({
          type,
          title,
          description,
        });
      }
    },
    [toastApi]
  );

  const [ticket, setTicket] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [loadError, setLoadError] = useState("");
  const [initialLoading, setInitialLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [assignmentSubmitting, setAssignmentSubmitting] = useState(false);
  const [reviewDecision, setReviewDecision] = useState("accepted");
  const [reviewReason, setReviewReason] = useState("");
  const [assignmentValue, setAssignmentValue] = useState("");

  const fetchTicket = useCallback(
    async ({ silent = false } = {}) => {
      if (!ticketId) {
        setLoadError("Die Ticket-ID fehlt.");
        setInitialLoading(false);
        return;
      }

      if (silent) {
        setRefreshing(true);
      } else {
        setInitialLoading(true);
      }

      try {
        const response = await api.get(`/tickets/${ticketId}`);
        const normalized = normalizeTicket(response.data);
        setTicket(normalized);
        setAssignmentValue(normalized?.assignee ?? "");
        setReviewDecision(normalized?.reviewDecision ?? "accepted");
        setReviewReason(normalized?.reviewReason ?? "");
        setLoadError("");
      } catch (error) {
        const message = readErrorMessage(error);
        setLoadError(message);
        emitToast({
          type: "error",
          title: "Ticket konnte nicht geladen werden",
          description: message,
        });
      } finally {
        setInitialLoading(false);
        setRefreshing(false);
      }
    },
    [ticketId, emitToast]
  );

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  const detailBadges = useMemo(
    () => [
      {
        label: formatStatus(ticket?.status || "open"),
        variant: "neutral",
      },
      {
        label: `Kategorie: ${formatCategory(ticket?.category)}`,
        variant: "info",
      },
      {
        label: `Priorität: ${formatPriority(ticket?.priority)}`,
        variant: "warning",
      },
      {
        label: `Trefferquote: ${formatConfidence(ticket?.confidence)}`,
        variant: "success",
      },
    ],
    [ticket]
  );

  const handleReviewSubmit = async (event) => {
    event.preventDefault();

    if (!ticket?.id) {
      emitToast({
        type: "error",
        title: "Prüfung fehlgeschlagen",
        description: "Aktuell ist kein Ticket geladen.",
      });
      return;
    }

    const normalizedCategory = (ticket.category || "bug").toLowerCase();
    const normalizedPriority = (ticket.priority || "medium").toLowerCase();

    setReviewSubmitting(true);

    try {
      await api.post("/tickets/decision", {
        ticket_id: ticket.id,
        final_category: normalizedCategory,
        final_priority: normalizedPriority,
        final_team: assignmentValue.trim() || ticket.assignee || "triage-team",
        accepted_ai_suggestion: reviewDecision === "accepted",
        review_comment: reviewReason,
        reviewed_by: "claudio",
      });

      emitToast({
        type: "success",
        title: "Prüfung gespeichert",
        description: `Der Entscheid "${formatReviewDecision(reviewDecision)}" wurde gespeichert.`,
      });

      await fetchTicket({ silent: true });
    } catch (error) {
      emitToast({
        type: "error",
        title: "Prüfung fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleAssignmentSubmit = async (event) => {
    event.preventDefault();

    if (!ticket?.id) {
      emitToast({
        type: "error",
        title: "Zuweisung fehlgeschlagen",
        description: "Aktuell ist kein Ticket geladen.",
      });
      return;
    }

    if (!assignmentValue.trim()) {
      emitToast({
        type: "error",
        title: "Zuweisung fehlgeschlagen",
        description: "Bitte gib vor dem Speichern ein Team oder eine zuständige Person ein.",
      });
      return;
    }

    setAssignmentSubmitting(true);

    try {
      await api.post("/tickets/assign", {
        ticket_id: ticket.id,
        assigned_team: assignmentValue.trim(),
        assigned_by: "claudio",
        assignment_note: "Zuweisung aus der Ticketdetailansicht",
      });

      emitToast({
        type: "success",
        title: "Zuweisung gespeichert",
        description: `Das Ticket wurde ${assignmentValue.trim()} zugewiesen.`,
      });

      await fetchTicket({ silent: true });
    } catch (error) {
      emitToast({
        type: "error",
        title: "Zuweisung fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setAssignmentSubmitting(false);
    }
  };

  const handleRefresh = async () => {
    await fetchTicket({ silent: true });
    emitToast({
      type: "success",
      title: "Ticket aktualisiert",
      description: "Die neuesten Ticketdaten werden jetzt angezeigt.",
    });
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(String(ticket?.id ?? ""));
      emitToast({
        type: "success",
        title: "Ticket-ID kopiert",
        description: `${ticket?.id} wurde in die Zwischenablage kopiert.`,
      });
    } catch {
      emitToast({
        type: "error",
        title: "Kopieren fehlgeschlagen",
        description: "Der Zugriff auf die Zwischenablage ist in diesem Browser nicht verfügbar.",
      });
    }
  };

  if (initialLoading) {
    return (
      <div className="ticket-detail-shell">
        <div className="detail-loading-state">
          <div className="detail-loading-spinner" />
          <div>
            <h2>Ticketdetails werden geladen</h2>
            <p>Die neuesten Prüf-, Zuweisungs- und KI-Triage-Daten werden geladen.</p>
          </div>
        </div>
      </div>
    );
  }

  if (!ticket) {
    return (
      <div className="ticket-detail-shell">
        <div className="detail-page-topbar">
          <Link className="detail-back-link" to="/">
            ← Zurück zum Dashboard
          </Link>
        </div>

        {loadError ? (
          <MessageBanner variant="error" title="Ticket nicht verfügbar">
            {loadError}
          </MessageBanner>
        ) : null}

        <div className="detail-empty-state detail-empty-state-large">
          <strong>Ticket nicht gefunden</strong>
          <p>
            Für die ID <code>{ticketId}</code> konnten keine Ticketdetails geladen werden.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="ticket-detail-shell">
      <div className="detail-page-topbar">
        <Link className="detail-back-link" to="/">
          ← Zurück zum Dashboard
        </Link>

        <div className="detail-action-row">
          <button
            className="detail-action-button detail-action-button-secondary"
            type="button"
            onClick={() => setActiveTab("review")}
          >
            Prüfung
          </button>
          <button
            className="detail-action-button detail-action-button-secondary"
            type="button"
            onClick={() => setActiveTab("assignment")}
          >
            Zuweisung
          </button>
          <button
            className="detail-action-button detail-action-button-secondary"
            type="button"
            onClick={handleCopyId}
          >
            ID kopieren
          </button>
          <button
            className="detail-action-button detail-action-button-primary"
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? "Aktualisiere..." : "Aktualisieren"}
          </button>
        </div>
      </div>

      {loadError ? (
        <MessageBanner variant="warning" title="Letzte erfolgreich geladene Ticketdaten werden verwendet">
          {loadError}
        </MessageBanner>
      ) : null}

      <section className="ticket-detail-hero">
        <div>
          <p className="detail-eyebrow">Ticket #{ticket.id}</p>
          <h1>{formatLabel(ticket.title, "Unbenanntes Ticket")}</h1>
          <p className="detail-muted">
            {formatLabel(
              ticket.summary ?? ticket.description,
              "Für dieses Ticket ist noch keine Zusammenfassung verfügbar."
            )}
          </p>
        </div>

        <div className="ticket-detail-meta">
          {detailBadges.map((item) => (
            <Badge key={item.label} variant={item.variant}>
              {item.label}
            </Badge>
          ))}
        </div>
      </section>

      <section className="ticket-detail-grid">
        <SectionCard title="Ticket-Metadaten">
          <div className="detail-stats-grid">
            <InfoStat label="Status" value={formatStatus(ticket.status)} />
            <InfoStat
              label="Supportbereich"
              value={formatLabel(ticket.department, "Bank-IT Support")}
            />
            <InfoStat label="Kategorie" value={formatCategory(ticket.category)} />
            <InfoStat label="Priorität" value={formatPriority(ticket.priority)} />
            <InfoStat label="Trefferquote" value={formatConfidence(ticket.confidence)} />
            <InfoStat label="Zugewiesen an" value={formatLabel(ticket.assignee, "Noch nicht zugewiesen")} />
            <InfoStat label="Erstellt" value={formatLabel(ticket.createdAt)} />
            <InfoStat label="Aktualisiert" value={formatLabel(ticket.updatedAt)} />
            <InfoStat
              label="Prüfung"
              value={formatReviewDecision(ticket.reviewDecision || "pending")}
            />
          </div>
        </SectionCard>

        <SectionCard title="Ticketinhalt">
          {ticket.description ? (
            <div className="detail-content-block">
              <p>{ticket.description}</p>
            </div>
          ) : (
            <EmptyInline
              title="Keine Detailbeschreibung"
              text="Dieses Ticket hat aktuell keine ausführliche Beschreibung."
            />
          )}
        </SectionCard>
      </section>

      <section className="detail-tabs-shell">
        <div className="detail-tabs">
          {TABS.map((tab) => (
            <button
              key={tab.key}
              type="button"
              className={`detail-tab ${activeTab === tab.key ? "is-active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="detail-tab-panel">
          {activeTab === "overview" ? (
            <div className="ticket-detail-grid">
              <SectionCard title="KI-Empfehlung">
                {ticket.category || ticket.priority || ticket.confidence ? (
                  <div className="detail-stats-grid">
                    <InfoStat label="Empfohlene Kategorie" value={formatCategory(ticket.category)} />
                    <InfoStat label="Empfohlene Priorität" value={formatPriority(ticket.priority)} />
                    <InfoStat
                      label="Modell-Trefferquote"
                      value={formatConfidence(ticket.confidence)}
                    />
                    <InfoStat
                      label="Empfohlenes Team"
                      value={formatLabel(ticket.suggestedTeam, "Unbekannt")}
                    />
                    <InfoStat
                      label="Empfohlene Abteilung"
                      value={formatLabel(ticket.analysis?.suggested_department, "Unbekannt")}
                    />
                  </div>
                ) : (
                  <EmptyInline
                    title="Keine KI-Empfehlung verfügbar"
                    text="Für dieses Ticket liegt noch keine Triage-Empfehlung vor."
                  />
                )}
              </SectionCard>

              <SectionCard title="Begründung">
                {ticket.rationale || ticket.nextStep ? (
                  <div className="detail-stats-grid">
                    <InfoStat
                      label="Begründung"
                      value={formatLabel(ticket.rationale, "Keine Begründung vorhanden")}
                    />
                    <InfoStat
                      label="Nächster Schritt"
                      value={formatLabel(ticket.nextStep, "Kein nächster Schritt vorhanden")}
                    />
                  </div>
                ) : (
                  <EmptyInline
                    title="Keine Begründung verfügbar"
                    text="Die KI hat für diese Ticketempfehlung keine Begründung geliefert."
                  />
                )}
              </SectionCard>

              <SectionCard title="Aktueller Entscheidungsstand">
                {ticket.reviewDecision || ticket.reviewReason || ticket.assignee ? (
                  <div className="detail-stats-grid">
                    <InfoStat
                      label="Prüfentscheid"
                      value={formatReviewDecision(ticket.reviewDecision || "pending")}
                    />
                    <InfoStat
                      label="Prüfnotizen"
                      value={formatLabel(ticket.reviewReason, "Keine Prüfnotizen")}
                    />
                    <InfoStat
                      label="Zugewiesen an"
                      value={formatLabel(ticket.assignee, "Noch nicht zugewiesen")}
                    />
                  </div>
                ) : (
                  <EmptyInline
                    title="Noch keine operativen Aktualisierungen"
                    text="Dieses Ticket wurde noch nicht geprüft oder zugewiesen."
                  />
                )}
              </SectionCard>

              <SectionCard title="Verlauf & Audit-Trail">
                {ticket.events.length ? (
                  <div className="detail-events-list">
                    {ticket.events.map((event) => (
                      <EventItem key={event.id} event={event} />
                    ))}
                  </div>
                ) : (
                  <EmptyInline
                    title="Kein Verlauf verfügbar"
                    text="Für dieses Ticket sind noch keine Audit-Ereignisse vorhanden."
                  />
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "review" ? (
            <SectionCard title="Prüfentscheid">
              <form className="detail-form" onSubmit={handleReviewSubmit}>
                <label className="detail-form-field">
                  <span>Entscheid</span>
                  <select
                    value={reviewDecision}
                    onChange={(event) => setReviewDecision(event.target.value)}
                    disabled={reviewSubmitting}
                  >
                    <option value="accepted">Akzeptieren</option>
                    <option value="rejected">Ablehnen</option>
                    <option value="needs_review">Weitere Prüfung nötig</option>
                    <option value="escalated">Eskalieren</option>
                  </select>
                </label>

                <label className="detail-form-field">
                  <span>Begründung / Notizen</span>
                  <textarea
                    rows="5"
                    placeholder="Prüfbegründung oder Korrekturhinweise ergänzen..."
                    value={reviewReason}
                    onChange={(event) => setReviewReason(event.target.value)}
                    disabled={reviewSubmitting}
                  />
                </label>

                <div className="detail-action-row">
                  <button
                    className="primary-button"
                    type="submit"
                    disabled={reviewSubmitting}
                  >
                    {reviewSubmitting ? "Speichere Prüfung..." : "Prüfung speichern"}
                  </button>
                </div>
              </form>
            </SectionCard>
          ) : null}

          {activeTab === "assignment" ? (
            <SectionCard title="Zuweisung">
              <form className="detail-form" onSubmit={handleAssignmentSubmit}>
                <label className="detail-form-field">
                  <span>Zuständiges Team / Person</span>
                  <input
                    type="text"
                    placeholder="z. B. it-support-team"
                    value={assignmentValue}
                    onChange={(event) => setAssignmentValue(event.target.value)}
                    disabled={assignmentSubmitting}
                  />
                </label>

                <div className="detail-action-row">
                  <button
                    className="primary-button"
                    type="submit"
                    disabled={assignmentSubmitting}
                  >
                    {assignmentSubmitting ? "Speichere Zuweisung..." : "Zuweisung speichern"}
                  </button>
                </div>
              </form>
            </SectionCard>
          ) : null}
        </div>
      </section>
    </div>
  );
}
