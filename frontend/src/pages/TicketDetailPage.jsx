import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import * as ToastModule from "../components/ToastProvider";
import Badge from "../components/Badge";
import MessageBanner from "../components/MessageBanner";
import SectionCard from "../components/SectionCard";
import { api } from "../lib/api";

const TABS = [
  { key: "overview", label: "Overview" },
  { key: "review", label: "Review" },
  { key: "assignment", label: "Assignment" },
];

function readErrorMessage(error) {
  return (
    error?.response?.data?.detail ||
    error?.response?.data?.message ||
    error?.message ||
    "An unexpected error occurred."
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

function formatLabel(value, fallback = "Not available") {
  return pickFirst(value) ?? fallback;
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
    ticket.ai_prediction?.category
  );

  const finalPriority = pickFirst(
    ticket.final_priority,
    ticket.priority,
    ticket.predicted_priority,
    ticket.ai_priority,
    ticket.ai_prediction?.priority
  );

  const assignee = pickFirst(
    ticket.assigned_to,
    ticket.assignee,
    ticket.owner,
    ticket.final_assignee
  );

  const confidence = pickFirst(
    ticket.confidence,
    ticket.ai_confidence,
    ticket.prediction_confidence,
    ticket.ai_prediction?.confidence
  );

  const summary = pickFirst(
    ticket.summary,
    ticket.ai_summary,
    ticket.generated_summary
  );

  const description = pickFirst(
    ticket.description,
    ticket.body,
    ticket.text,
    ticket.content
  );

  const title = pickFirst(
    ticket.title,
    ticket.subject,
    summary,
    `Ticket #${pickFirst(ticket.id, ticket.ticket_id, "Unknown")}`
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
    ticket.decision
  );

  const reviewReason = pickFirst(
    ticket.review_reason,
    ticket.reason,
    ticket.notes
  );

  return {
    raw: ticket,
    id: pickFirst(ticket.id, ticket.ticket_id, "Unknown"),
    title,
    description,
    summary,
    category: finalCategory,
    priority: finalPriority,
    assignee,
    confidence,
    status,
    createdAt,
    updatedAt,
    reviewDecision,
    reviewReason,
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
        setLoadError("Ticket ID is missing.");
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
          title: "Ticket could not be loaded",
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
        label: formatLabel(ticket?.status, "Open"),
        variant: "neutral",
      },
      {
        label: `Category: ${formatLabel(ticket?.category)}`,
        variant: "info",
      },
      {
        label: `Priority: ${formatLabel(ticket?.priority)}`,
        variant: "warning",
      },
      {
        label: `Confidence: ${formatConfidence(ticket?.confidence)}`,
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
        title: "Review failed",
        description: "No ticket is currently loaded.",
      });
      return;
    }

    setReviewSubmitting(true);

    try {
      await api.post("/tickets/decision", {
        ticket_id: ticket.id,
        decision: reviewDecision,
        review_decision: reviewDecision,
        reason: reviewReason,
        notes: reviewReason,
      });

      emitToast({
        type: "success",
        title: "Review saved",
        description: `Decision "${reviewDecision}" was stored successfully.`,
      });

      await fetchTicket({ silent: true });
    } catch (error) {
      emitToast({
        type: "error",
        title: "Review failed",
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
        title: "Assignment failed",
        description: "No ticket is currently loaded.",
      });
      return;
    }

    if (!assignmentValue.trim()) {
      emitToast({
        type: "error",
        title: "Assignment failed",
        description: "Please enter an assignee before saving.",
      });
      return;
    }

    setAssignmentSubmitting(true);

    try {
      await api.post("/tickets/assign", {
        ticket_id: ticket.id,
        assigned_to: assignmentValue.trim(),
        assignee: assignmentValue.trim(),
      });

      emitToast({
        type: "success",
        title: "Assignment saved",
        description: `Ticket assigned to ${assignmentValue.trim()}.`,
      });

      await fetchTicket({ silent: true });
    } catch (error) {
      emitToast({
        type: "error",
        title: "Assignment failed",
        description: readErrorMessage(error),
      });
    } finally {
      setAssignmentSubmitting(false);
    }
  };

  const handleRefresh = async () => {
    await fetchTicket({ silent: true });
    if (!loadError) {
      emitToast({
        type: "success",
        title: "Ticket refreshed",
        description: "The latest ticket data is now displayed.",
      });
    }
  };

  const handleCopyId = async () => {
    try {
      await navigator.clipboard.writeText(String(ticket?.id ?? ""));
      emitToast({
        type: "success",
        title: "Ticket ID copied",
        description: `Copied ${ticket?.id} to clipboard.`,
      });
    } catch {
      emitToast({
        type: "error",
        title: "Copy failed",
        description: "Clipboard access is not available in this browser.",
      });
    }
  };

  if (initialLoading) {
    return (
      <div className="ticket-detail-shell">
        <div className="detail-loading-state">
          <div className="detail-loading-spinner" />
          <div>
            <h2>Loading ticket details</h2>
            <p>Fetching the latest review, assignment and AI triage data.</p>
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
            ← Back to dashboard
          </Link>
        </div>

        {loadError ? (
          <MessageBanner variant="error" title="Ticket unavailable">
            {loadError}
          </MessageBanner>
        ) : null}

        <div className="detail-empty-state detail-empty-state-large">
          <strong>Ticket not found</strong>
          <p>
            No ticket details could be loaded for ID <code>{ticketId}</code>.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="ticket-detail-shell">
      <div className="detail-page-topbar">
        <Link className="detail-back-link" to="/">
          ← Back to dashboard
        </Link>

        <div className="detail-action-row">
          <button
            className="secondary-button"
            type="button"
            onClick={() => setActiveTab("review")}
          >
            Review
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={() => setActiveTab("assignment")}
          >
            Assign
          </button>
          <button
            className="secondary-button"
            type="button"
            onClick={handleCopyId}
          >
            Copy ID
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {loadError ? (
        <MessageBanner variant="warning" title="Using last successful ticket data">
          {loadError}
        </MessageBanner>
      ) : null}

      <section className="ticket-detail-hero">
        <div>
          <p className="detail-eyebrow">Ticket #{ticket.id}</p>
          <h1>{formatLabel(ticket.title, "Untitled ticket")}</h1>
          <p className="detail-muted">
            {formatLabel(
              ticket.summary ?? ticket.description,
              "No summary is available for this ticket yet."
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
        <SectionCard title="Ticket metadata">
          <div className="detail-stats-grid">
            <InfoStat label="Status" value={formatLabel(ticket.status, "Open")} />
            <InfoStat label="Category" value={formatLabel(ticket.category)} />
            <InfoStat label="Priority" value={formatLabel(ticket.priority)} />
            <InfoStat label="Confidence" value={formatConfidence(ticket.confidence)} />
            <InfoStat label="Assignee" value={formatLabel(ticket.assignee, "Unassigned")} />
            <InfoStat label="Created" value={formatLabel(ticket.createdAt)} />
            <InfoStat label="Updated" value={formatLabel(ticket.updatedAt)} />
            <InfoStat
              label="Review"
              value={formatLabel(ticket.reviewDecision, "Pending review")}
            />
          </div>
        </SectionCard>

        <SectionCard title="Ticket content">
          {ticket.description ? (
            <div className="detail-content-block">
              <p>{ticket.description}</p>
            </div>
          ) : (
            <EmptyInline
              title="No detailed description"
              text="This ticket currently has no long-form description."
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
              <SectionCard title="AI recommendation">
                {ticket.category || ticket.priority || ticket.confidence ? (
                  <div className="detail-stats-grid">
                    <InfoStat label="Suggested category" value={formatLabel(ticket.category)} />
                    <InfoStat label="Suggested priority" value={formatLabel(ticket.priority)} />
                    <InfoStat
                      label="Model confidence"
                      value={formatConfidence(ticket.confidence)}
                    />
                  </div>
                ) : (
                  <EmptyInline
                    title="No AI recommendation available"
                    text="The ticket has not received a triage recommendation yet."
                  />
                )}
              </SectionCard>

              <SectionCard title="Current decision context">
                {ticket.reviewDecision || ticket.reviewReason || ticket.assignee ? (
                  <div className="detail-stats-grid">
                    <InfoStat
                      label="Review decision"
                      value={formatLabel(ticket.reviewDecision, "Pending")}
                    />
                    <InfoStat
                      label="Review notes"
                      value={formatLabel(ticket.reviewReason, "No review notes")}
                    />
                    <InfoStat
                      label="Assigned to"
                      value={formatLabel(ticket.assignee, "Unassigned")}
                    />
                  </div>
                ) : (
                  <EmptyInline
                    title="No operational updates yet"
                    text="This ticket has not been reviewed or assigned yet."
                  />
                )}
              </SectionCard>
            </div>
          ) : null}

          {activeTab === "review" ? (
            <SectionCard title="Review decision">
              <form className="detail-form" onSubmit={handleReviewSubmit}>
                <label className="detail-form-field">
                  <span>Decision</span>
                  <select
                    value={reviewDecision}
                    onChange={(event) => setReviewDecision(event.target.value)}
                    disabled={reviewSubmitting}
                  >
                    <option value="accepted">Accept</option>
                    <option value="rejected">Reject</option>
                    <option value="needs_review">Needs review</option>
                    <option value="escalated">Escalate</option>
                  </select>
                </label>

                <label className="detail-form-field">
                  <span>Reason / notes</span>
                  <textarea
                    rows="5"
                    placeholder="Add reviewer rationale or corrective notes..."
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
                    {reviewSubmitting ? "Saving review..." : "Save review"}
                  </button>
                </div>
              </form>
            </SectionCard>
          ) : null}

          {activeTab === "assignment" ? (
            <SectionCard title="Assignment">
              <form className="detail-form" onSubmit={handleAssignmentSubmit}>
                <label className="detail-form-field">
                  <span>Assignee</span>
                  <input
                    type="text"
                    placeholder="e.g. product-team@company.com"
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
                    {assignmentSubmitting ? "Saving assignment..." : "Save assignment"}
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
