import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import ActivityTimeline from "../components/ActivityTimeline";
import AssigneePicker from "../components/AssigneePicker";
import Badge from "../components/Badge";
import CommentComposer from "../components/CommentComposer";
import MessageBanner from "../components/MessageBanner";
import SectionCard from "../components/SectionCard";
import SlaBadge from "../components/SlaBadge";
import * as ToastModule from "../components/ToastProvider";
import {
  addTicketComment,
  assignTicket,
  escalateTicket,
  fetchTicket,
  saveDecision,
  updateTicketStatus,
} from "../lib/api";
import { getOperatorName } from "../lib/userSettings";

const TABS = [
  { key: "overview", label: "Übersicht" },
  { key: "review", label: "Prüfung" },
  { key: "assignment", label: "Zuweisung" },
];

const CATEGORY_OPTIONS = [
  { value: "bug", label: "Fehler" },
  { value: "feature", label: "Funktion" },
  { value: "support", label: "Support" },
  { value: "requirement", label: "Anforderung" },
  { value: "question", label: "Frage" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Niedrig" },
  { value: "medium", label: "Mittel" },
  { value: "high", label: "Hoch" },
  { value: "critical", label: "Kritisch" },
];

const STATUS_OPTIONS = [
  { value: "new", label: "Neu" },
  { value: "triaged", label: "Triagiert" },
  { value: "reviewed", label: "Geprüft" },
  { value: "assigned", label: "Zugewiesen" },
  { value: "closed", label: "Geschlossen" },
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

  return new Intl.DateTimeFormat("de-CH", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
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

function formatTags(tags) {
  if (!Array.isArray(tags) || !tags.length) {
    return "Keine Tags";
  }

  return tags.join(", ");
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
      closed: "Geschlossen",
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

function normalizeTicket(ticket) {
  if (!ticket || typeof ticket !== "object") {
    return null;
  }

  const category = pickFirst(
    ticket.final_category,
    ticket.category,
    ticket.decision?.final_category,
    ticket.analysis?.predicted_category,
    "unknown"
  );
  const priority = pickFirst(
    ticket.final_priority,
    ticket.priority,
    ticket.decision?.final_priority,
    ticket.analysis?.predicted_priority,
    "medium"
  );
  const team = pickFirst(
    ticket.team,
    ticket.assignment?.assigned_team,
    ticket.decision?.final_team,
    ticket.analysis?.suggested_team
  );
  const assignee = pickFirst(
    ticket.assignee,
    ticket.assignment?.assignee,
    ticket.owner,
    ticket.assigned_to
  );
  const reviewDecision = ticket.decision
    ? ticket.decision.accepted_ai_suggestion
      ? "accepted"
      : "rejected"
    : "pending";

  return {
    raw: ticket,
    id: pickFirst(ticket.id, ticket.ticket_id, ticket.ticketId, "Unknown"),
    title: pickFirst(ticket.title, ticket.subject, "Unbenanntes Ticket"),
    description: pickFirst(ticket.description, ticket.body, ticket.text),
    summary: pickFirst(ticket.analysis?.summary, ticket.summary),
    reporter: pickFirst(ticket.reporter),
    department: pickFirst(
      ticket.department,
      ticket.analysis?.suggested_department,
      "Bank-IT Support"
    ),
    category,
    priority,
    predictedCategory: pickFirst(ticket.analysis?.predicted_category),
    predictedPriority: pickFirst(ticket.analysis?.predicted_priority),
    suggestedDepartment: pickFirst(ticket.analysis?.suggested_department, ticket.department),
    suggestedTeam: pickFirst(ticket.analysis?.suggested_team),
    rationale: pickFirst(ticket.analysis?.rationale),
    nextStep: pickFirst(ticket.analysis?.next_step),
    confidence: pickFirst(ticket.analysis?.category_confidence),
    team,
    assignee,
    dueAt: pickFirst(ticket.due_at, ticket.dueAt),
    tags: Array.isArray(ticket.tags) ? ticket.tags : [],
    slaBreached: Boolean(ticket.sla_breached ?? ticket.slaBreached),
    status: pickFirst(ticket.status, "new"),
    createdAt: pickFirst(ticket.created_at, ticket.createdAt),
    updatedAt: pickFirst(ticket.updated_at, ticket.updatedAt, ticket.created_at),
    reviewDecision,
    reviewReason: pickFirst(ticket.decision?.review_comment),
    events: Array.isArray(ticket.events) ? ticket.events.map(normalizeEvent) : [],
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

export default function TicketDetailPage() {
  const { ticketId } = useParams();
  const toastApi = ToastModule.useToast?.() ?? null;
  const currentOperator = useMemo(() => getOperatorName(), []);

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

      toastApi?.showToast?.({
        type,
        title,
        message: description,
      });
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
  const [statusSubmitting, setStatusSubmitting] = useState(false);
  const [commentSubmitting, setCommentSubmitting] = useState(false);
  const [escalating, setEscalating] = useState(false);

  const [reviewForm, setReviewForm] = useState({
    decision: "accepted",
    category: "bug",
    priority: "medium",
    team: "",
    reason: "",
  });
  const [assignmentForm, setAssignmentForm] = useState({
    team: "",
    assignee: "",
    note: "",
  });
  const [statusForm, setStatusForm] = useState({
    status: "triaged",
    note: "",
  });

  const hydrateForms = useCallback((normalizedTicket) => {
    if (!normalizedTicket) {
      return;
    }

    setReviewForm({
      decision: normalizedTicket.reviewDecision || "accepted",
      category: normalizedTicket.category || "bug",
      priority: normalizedTicket.priority || "medium",
      team: normalizedTicket.team || normalizedTicket.suggestedTeam || "",
      reason: normalizedTicket.reviewReason || "",
    });
    setAssignmentForm({
      team: normalizedTicket.team || normalizedTicket.suggestedTeam || "",
      assignee: normalizedTicket.assignee || "",
      note: "",
    });
    setStatusForm({
      status: normalizedTicket.status || "triaged",
      note: "",
    });
  }, []);

  const loadTicket = useCallback(
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
        const response = await fetchTicket(ticketId);
        const normalizedTicket = normalizeTicket(response);
        setTicket(normalizedTicket);
        hydrateForms(normalizedTicket);
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
    [emitToast, hydrateForms, ticketId]
  );

  useEffect(() => {
    loadTicket();
  }, [loadTicket]);

  const detailBadges = useMemo(() => {
    if (!ticket) {
      return [];
    }

    return [
      { value: ticket.status, type: "status" },
      { value: ticket.category, type: "category" },
      { value: ticket.priority, type: "priority" },
    ];
  }, [ticket]);

  async function refreshWithSuccess(title, description) {
    await loadTicket({ silent: true });
    emitToast({
      type: "success",
      title,
      description,
    });
  }

  async function handleReviewSubmit(event) {
    event.preventDefault();

    if (!ticket?.id) {
      return;
    }

    setReviewSubmitting(true);

    try {
      await saveDecision({
        ticket_id: ticket.id,
        final_category: reviewForm.category,
        final_priority: reviewForm.priority,
        final_team: reviewForm.team.trim() || ticket.team || ticket.suggestedTeam || "triage-team",
        accepted_ai_suggestion: reviewForm.decision === "accepted",
        review_comment: reviewForm.reason.trim() || null,
        reviewed_by: currentOperator,
      });

      if (reviewForm.decision === "escalated") {
        await escalateTicket({
          ticket_id: ticket.id,
          escalated_by: currentOperator,
          reason: reviewForm.reason.trim() || "Eskalation aus der Prüfentscheidung",
          target_team: assignmentForm.team.trim() || reviewForm.team.trim() || ticket.team || null,
          assignee: assignmentForm.assignee.trim() || ticket.assignee || null,
          priority: "critical",
        });
      }

      await refreshWithSuccess(
        "Prüfung gespeichert",
        `Der Entscheid "${formatReviewDecision(reviewForm.decision)}" wurde übernommen.`
      );
    } catch (error) {
      emitToast({
        type: "error",
        title: "Prüfung fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setReviewSubmitting(false);
    }
  }

  async function handleAssignmentSubmit(event) {
    event.preventDefault();

    if (!ticket?.id) {
      return;
    }

    if (!assignmentForm.team.trim()) {
      emitToast({
        type: "error",
        title: "Zuweisung fehlgeschlagen",
        description: "Bitte hinterlege mindestens ein zuständiges Team.",
      });
      return;
    }

    setAssignmentSubmitting(true);

    try {
      await assignTicket({
        ticket_id: ticket.id,
        assigned_team: assignmentForm.team.trim(),
        assignee: assignmentForm.assignee.trim() || null,
        assigned_by: currentOperator,
        assignment_note: assignmentForm.note.trim() || "Zuweisung aus der Ticketdetailansicht",
      });

      await refreshWithSuccess(
        "Zuweisung gespeichert",
        `Das Ticket wurde ${assignmentForm.team.trim()} zugewiesen.`
      );
    } catch (error) {
      emitToast({
        type: "error",
        title: "Zuweisung fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setAssignmentSubmitting(false);
    }
  }

  async function handleStatusSubmit(event) {
    event.preventDefault();

    if (!ticket?.id) {
      return;
    }

    setStatusSubmitting(true);

    try {
      await updateTicketStatus({
        ticket_id: ticket.id,
        status: statusForm.status,
        actor: currentOperator,
        note: statusForm.note.trim() || null,
      });

      await refreshWithSuccess(
        "Status aktualisiert",
        `Der Ticketstatus ist jetzt ${formatStatus(statusForm.status)}.`
      );
    } catch (error) {
      emitToast({
        type: "error",
        title: "Statusänderung fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setStatusSubmitting(false);
    }
  }

  async function handleCloseTicket() {
    if (!ticket?.id) {
      return;
    }

    setStatusSubmitting(true);

    try {
      await updateTicketStatus({
        ticket_id: ticket.id,
        status: "closed",
        actor: currentOperator,
        note: statusForm.note.trim() || "Ticket manuell abgeschlossen",
      });

      await refreshWithSuccess(
        "Ticket geschlossen",
        "Das Ticket wurde als abgeschlossen markiert."
      );
    } catch (error) {
      emitToast({
        type: "error",
        title: "Schliessen fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setStatusSubmitting(false);
    }
  }

  async function handleEscalateTicket() {
    if (!ticket?.id) {
      return;
    }

    if (!reviewForm.reason.trim()) {
      emitToast({
        type: "error",
        title: "Eskalation braucht einen Grund",
        description: "Bitte hinterlege vor der Eskalation eine kurze Begründung im Prüfbereich.",
      });
      setActiveTab("review");
      return;
    }

    setEscalating(true);

    try {
      await escalateTicket({
        ticket_id: ticket.id,
        escalated_by: currentOperator,
        reason: reviewForm.reason.trim(),
        target_team: assignmentForm.team.trim() || reviewForm.team.trim() || ticket.team || null,
        assignee: assignmentForm.assignee.trim() || ticket.assignee || null,
        priority: "critical",
      });

      await refreshWithSuccess(
        "Ticket eskaliert",
        "Priorität und SLA-Status wurden für die Eskalation angepasst."
      );
    } catch (error) {
      emitToast({
        type: "error",
        title: "Eskalation fehlgeschlagen",
        description: readErrorMessage(error),
      });
    } finally {
      setEscalating(false);
    }
  }

  async function handleCommentSubmit(payload) {
    if (!ticket?.id) {
      return false;
    }

    setCommentSubmitting(true);

    try {
      await addTicketComment({
        ticket_id: ticket.id,
        actor: payload.actor || currentOperator,
        body: payload.body,
        is_internal: payload.isInternal,
      });

      await refreshWithSuccess(
        payload.isInternal ? "Interne Notiz gespeichert" : "Kommentar gespeichert",
        "Der Verlauf wurde aktualisiert."
      );
      return true;
    } catch (error) {
      emitToast({
        type: "error",
        title: "Kommentar fehlgeschlagen",
        description: readErrorMessage(error),
      });
      return false;
    } finally {
      setCommentSubmitting(false);
    }
  }

  async function handleRefresh() {
    await loadTicket({ silent: true });
    emitToast({
      type: "success",
      title: "Ticket aktualisiert",
      description: "Die neuesten Ticketdaten werden jetzt angezeigt.",
    });
  }

  async function handleCopyId() {
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
  }

  if (initialLoading) {
    return (
      <div className="ticket-detail-shell">
        <div className="detail-loading-state">
          <div className="detail-loading-spinner" />
          <div>
            <h2>Ticketdetails werden geladen</h2>
            <p>Prüfung, Zuweisung, Kommentare und Audit-Trail werden vorbereitet.</p>
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
            className="detail-action-button detail-action-button-danger"
            type="button"
            onClick={handleEscalateTicket}
            disabled={escalating}
          >
            {escalating ? "Eskaliere..." : "Eskalieren"}
          </button>
          <button
            className="detail-action-button detail-action-button-secondary"
            type="button"
            onClick={handleCloseTicket}
            disabled={statusSubmitting || ticket.status === "closed"}
          >
            Schliessen
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

      {ticket.status === "closed" ? (
        <MessageBanner variant="success" title="Ticket ist abgeschlossen">
          Dieses Ticket wurde geschlossen. Kommentare und Verlauf bleiben weiterhin sichtbar.
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
            <Badge key={`${item.type}-${item.value}`} value={item.value} type={item.type} />
          ))}
          <SlaBadge dueAt={ticket.dueAt} breached={ticket.slaBreached} />
        </div>
      </section>

      <section className="ticket-detail-grid">
        <SectionCard title="Ticket-Metadaten">
          <div className="detail-stats-grid">
            <InfoStat label="Status" value={formatStatus(ticket.status)} />
            <InfoStat label="Supportbereich" value={formatLabel(ticket.department, "Bank-IT Support")} />
            <InfoStat label="Team" value={formatLabel(ticket.team, "Noch offen")} />
            <InfoStat label="Kategorie" value={formatCategory(ticket.category)} />
            <InfoStat label="Priorität" value={formatPriority(ticket.priority)} />
            <InfoStat label="Trefferquote" value={formatConfidence(ticket.confidence)} />
            <InfoStat label="Zugewiesen an" value={formatLabel(ticket.assignee, "Noch nicht zugewiesen")} />
            <InfoStat label="Erstellt" value={formatLabel(ticket.createdAt ? formatDateTime(ticket.createdAt) : null)} />
            <InfoStat label="Aktualisiert" value={formatLabel(ticket.updatedAt ? formatDateTime(ticket.updatedAt) : null)} />
            <InfoStat label="Fällig am" value={formatLabel(ticket.dueAt ? formatDateTime(ticket.dueAt) : null, "Noch nicht definiert")} />
            <InfoStat label="SLA" value={ticket.slaBreached ? "Verletzt" : "Im Rahmen"} />
            <InfoStat label="Tags" value={formatTags(ticket.tags)} />
            <InfoStat label="Reporter" value={formatLabel(ticket.reporter, "Nicht hinterlegt")} />
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
                {ticket.predictedCategory || ticket.predictedPriority || ticket.confidence ? (
                  <div className="detail-stats-grid">
                    <InfoStat label="Empfohlene Kategorie" value={formatCategory(ticket.predictedCategory)} />
                    <InfoStat label="Empfohlene Priorität" value={formatPriority(ticket.predictedPriority)} />
                    <InfoStat label="Modell-Trefferquote" value={formatConfidence(ticket.confidence)} />
                    <InfoStat label="Empfohlenes Team" value={formatLabel(ticket.suggestedTeam, "Unbekannt")} />
                    <InfoStat label="Empfohlene Abteilung" value={formatLabel(ticket.suggestedDepartment, "Unbekannt")} />
                    <InfoStat label="Nächster Schritt" value={formatLabel(ticket.nextStep, "Kein nächster Schritt vorhanden")} />
                  </div>
                ) : (
                  <EmptyInline
                    title="Keine KI-Empfehlung verfügbar"
                    text="Für dieses Ticket liegt noch keine Triage-Empfehlung vor."
                  />
                )}
              </SectionCard>

              <SectionCard title="Status & SLA">
                <form className="detail-form" onSubmit={handleStatusSubmit}>
                  <label className="detail-form-field">
                    <span>Status</span>
                    <select
                      value={statusForm.status}
                      onChange={(event) => setStatusForm({ ...statusForm, status: event.target.value })}
                      disabled={statusSubmitting}
                    >
                      {STATUS_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </label>

                  <label className="detail-form-field">
                    <span>Operative Notiz</span>
                    <textarea
                      rows="4"
                      placeholder="Statuswechsel kurz begründen oder Zusatzkontext erfassen..."
                      value={statusForm.note}
                      onChange={(event) => setStatusForm({ ...statusForm, note: event.target.value })}
                      disabled={statusSubmitting}
                    />
                  </label>

                  <div className="detail-status-panel">
                    <div className="detail-status-panel-copy">
                      <strong>SLA-Lage</strong>
                      <SlaBadge dueAt={ticket.dueAt} breached={ticket.slaBreached} />
                    </div>
                    <button className="primary-button" type="submit" disabled={statusSubmitting}>
                      {statusSubmitting ? "Aktualisiere Status..." : "Status speichern"}
                    </button>
                  </div>
                </form>
              </SectionCard>

              <SectionCard title="Kommentare & interne Notizen">
                <CommentComposer
                  onSubmit={handleCommentSubmit}
                  submitting={commentSubmitting}
                  defaultActor={currentOperator}
                />
              </SectionCard>

              <SectionCard title="Verlauf & Audit-Trail">
                <ActivityTimeline events={ticket.events} />
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "review" ? (
            <SectionCard title="Prüfentscheid & Priorisierung">
              <form className="detail-form" onSubmit={handleReviewSubmit}>
                <label className="detail-form-field">
                  <span>Entscheid</span>
                  <select
                    value={reviewForm.decision}
                    onChange={(event) => setReviewForm({ ...reviewForm, decision: event.target.value })}
                    disabled={reviewSubmitting}
                  >
                    <option value="accepted">KI-Vorschlag akzeptieren</option>
                    <option value="rejected">KI-Vorschlag anpassen</option>
                    <option value="needs_review">Weitere Prüfung nötig</option>
                    <option value="escalated">Mit Eskalation speichern</option>
                  </select>
                </label>

                <label className="detail-form-field">
                  <span>Kategorie</span>
                  <select
                    value={reviewForm.category}
                    onChange={(event) => setReviewForm({ ...reviewForm, category: event.target.value })}
                    disabled={reviewSubmitting}
                  >
                    {CATEGORY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="detail-form-field">
                  <span>Priorität</span>
                  <select
                    value={reviewForm.priority}
                    onChange={(event) => setReviewForm({ ...reviewForm, priority: event.target.value })}
                    disabled={reviewSubmitting}
                  >
                    {PRIORITY_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>

                <label className="detail-form-field">
                  <span>Zielteam</span>
                  <input
                    type="text"
                    value={reviewForm.team}
                    onChange={(event) => setReviewForm({ ...reviewForm, team: event.target.value })}
                    placeholder="z. B. payments-operations-team"
                    disabled={reviewSubmitting}
                  />
                </label>

                <label className="detail-form-field">
                  <span>Begründung / Prüfnotiz</span>
                  <textarea
                    rows="5"
                    placeholder="Prüfbegründung, Korrektur oder Eskalationsgrund ergänzen..."
                    value={reviewForm.reason}
                    onChange={(event) => setReviewForm({ ...reviewForm, reason: event.target.value })}
                    disabled={reviewSubmitting}
                  />
                </label>

                <div className="detail-action-row">
                  <button className="primary-button" type="submit" disabled={reviewSubmitting}>
                    {reviewSubmitting ? "Speichere Prüfung..." : "Prüfung speichern"}
                  </button>
                </div>
              </form>
            </SectionCard>
          ) : null}

          {activeTab === "assignment" ? (
            <SectionCard title="Neu zuweisen">
              <AssigneePicker
                team={assignmentForm.team}
                assignee={assignmentForm.assignee}
                note={assignmentForm.note}
                submitting={assignmentSubmitting}
                onChange={(key, value) => setAssignmentForm((current) => ({ ...current, [key]: value }))}
                onSubmit={handleAssignmentSubmit}
              />
            </SectionCard>
          ) : null}
        </div>
      </section>
    </div>
  );
}
