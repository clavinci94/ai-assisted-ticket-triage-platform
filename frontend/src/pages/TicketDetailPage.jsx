import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Badge from "../components/Badge";
import LabelValue from "../components/LabelValue";
import MessageBanner from "../components/MessageBanner";
import SectionCard from "../components/SectionCard";
import LoadingState from "../components/LoadingState";
import EmptyState from "../components/EmptyState";
import { assignTicket, fetchTicket, saveDecision } from "../lib/api";

const CATEGORY_OPTIONS = ["bug", "feature", "support", "requirement", "question", "unknown"];
const PRIORITY_OPTIONS = ["low", "medium", "high", "critical"];
const TEAM_OPTIONS = ["engineering-team", "product-team", "support-team", "triage-team"];

const initialDecisionForm = {
  final_category: "bug",
  final_priority: "high",
  final_team: "engineering-team",
  accepted_ai_suggestion: true,
  review_comment: "",
  reviewed_by: "",
};

const initialAssignmentForm = {
  assigned_team: "engineering-team",
  assigned_by: "",
  assignment_note: "",
};

const tabs = ["overview", "analysis", "review", "assignment"];

function validateDecisionForm(form) {
  const errors = {};

  if (!CATEGORY_OPTIONS.includes(form.final_category)) {
    errors.final_category = "Please select a valid category.";
  }

  if (!PRIORITY_OPTIONS.includes(form.final_priority)) {
    errors.final_priority = "Please select a valid priority.";
  }

  if (!TEAM_OPTIONS.includes(form.final_team)) {
    errors.final_team = "Please select a valid team.";
  }

  if (form.reviewed_by && form.reviewed_by.trim().length > 100) {
    errors.reviewed_by = "Reviewed by must be 100 characters or fewer.";
  }

  if (form.review_comment && form.review_comment.trim().length > 1000) {
    errors.review_comment = "Review comment must be 1000 characters or fewer.";
  }

  return errors;
}

function validateAssignmentForm(form) {
  const errors = {};

  if (!TEAM_OPTIONS.includes(form.assigned_team)) {
    errors.assigned_team = "Please select a valid team.";
  }

  if (form.assigned_by && form.assigned_by.trim().length > 100) {
    errors.assigned_by = "Assigned by must be 100 characters or fewer.";
  }

  if (form.assignment_note && form.assignment_note.trim().length > 1000) {
    errors.assignment_note = "Assignment note must be 1000 characters or fewer.";
  }

  return errors;
}

function FieldError({ message }) {
  if (!message) return null;
  return <div className="field-error">{message}</div>;
}

export default function TicketDetailPage() {
  const { ticketId } = useParams();

  const [ticket, setTicket] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [decisionForm, setDecisionForm] = useState(initialDecisionForm);
  const [assignmentForm, setAssignmentForm] = useState(initialAssignmentForm);

  const [decisionErrors, setDecisionErrors] = useState({});
  const [assignmentErrors, setAssignmentErrors] = useState({});

  const [loading, setLoading] = useState(true);
  const [submittingDecision, setSubmittingDecision] = useState(false);
  const [submittingAssignment, setSubmittingAssignment] = useState(false);
  const [runningQuickAction, setRunningQuickAction] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function loadTicketData() {
    try {
      setLoading(true);
      setError("");
      const data = await fetchTicket(ticketId);
      setTicket(data);

      if (data?.decision) {
        setDecisionForm({
          final_category: data.decision.final_category || "bug",
          final_priority: data.decision.final_priority || "high",
          final_team: data.decision.final_team || "engineering-team",
          accepted_ai_suggestion: Boolean(data.decision.accepted_ai_suggestion),
          review_comment: data.decision.review_comment || "",
          reviewed_by: data.decision.reviewed_by || "",
        });
      } else if (data?.analysis) {
        setDecisionForm({
          final_category: data.analysis.predicted_category || "bug",
          final_priority: data.analysis.predicted_priority || "high",
          final_team: data.analysis.suggested_team || "engineering-team",
          accepted_ai_suggestion: true,
          review_comment: "",
          reviewed_by: "",
        });
      } else {
        setDecisionForm(initialDecisionForm);
      }

      if (data?.assignment) {
        setAssignmentForm({
          assigned_team: data.assignment.assigned_team || "engineering-team",
          assigned_by: data.assignment.assigned_by || "",
          assignment_note: data.assignment.assignment_note || "",
        });
      } else if (data?.analysis) {
        setAssignmentForm({
          assigned_team: data.analysis.suggested_team || "engineering-team",
          assigned_by: "",
          assignment_note: "",
        });
      } else {
        setAssignmentForm(initialAssignmentForm);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to load ticket.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadTicketData();
  }, [ticketId]);

  useEffect(() => {
    setDecisionErrors(validateDecisionForm(decisionForm));
  }, [decisionForm]);

  useEffect(() => {
    setAssignmentErrors(validateAssignmentForm(assignmentForm));
  }, [assignmentForm]);

  const decisionFormValid = useMemo(
    () => Object.keys(decisionErrors).length === 0,
    [decisionErrors]
  );

  const assignmentFormValid = useMemo(
    () => Object.keys(assignmentErrors).length === 0,
    [assignmentErrors]
  );

  function applyAiToDecisionForm() {
    if (!ticket?.analysis) return;

    setDecisionForm((prev) => ({
      ...prev,
      final_category: ticket.analysis.predicted_category || prev.final_category,
      final_priority: ticket.analysis.predicted_priority || prev.final_priority,
      final_team: ticket.analysis.suggested_team || prev.final_team,
      accepted_ai_suggestion: true,
    }));
    setSuccess("AI recommendation copied into the review form.");
    setError("");
  }

  function copyAiTeamToAssignmentForm() {
    if (!ticket?.analysis?.suggested_team) return;

    setAssignmentForm((prev) => ({
      ...prev,
      assigned_team: ticket.analysis.suggested_team,
    }));
    setSuccess("Suggested AI team copied into the assignment form.");
    setError("");
  }

  async function handleAcceptAiRecommendation() {
    if (!ticket?.analysis) return;

    try {
      setRunningQuickAction(true);
      setError("");
      setSuccess("");

      await saveDecision({
        ticket_id: ticketId,
        final_category: ticket.analysis.predicted_category,
        final_priority: ticket.analysis.predicted_priority,
        final_team: ticket.analysis.suggested_team,
        accepted_ai_suggestion: true,
        review_comment: "Accepted AI recommendation via quick action.",
        reviewed_by: decisionForm.reviewed_by.trim(),
      });

      await loadTicketData();
      setActiveTab("review");
      setSuccess("AI recommendation accepted and saved.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to accept AI recommendation.");
    } finally {
      setRunningQuickAction(false);
    }
  }

  async function handleAssignToSuggestedTeam() {
    if (!ticket?.analysis?.suggested_team) return;

    try {
      setRunningQuickAction(true);
      setError("");
      setSuccess("");

      await assignTicket({
        ticket_id: ticketId,
        assigned_team: ticket.analysis.suggested_team,
        assigned_by: assignmentForm.assigned_by.trim(),
        assignment_note:
          assignmentForm.assignment_note.trim() ||
          "Assigned to AI-suggested team via quick action.",
      });

      await loadTicketData();
      setActiveTab("assignment");
      setSuccess("Ticket assigned to the AI-suggested team.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to assign ticket to suggested team.");
    } finally {
      setRunningQuickAction(false);
    }
  }

  async function handleDecisionSubmit(e) {
    e.preventDefault();

    const errors = validateDecisionForm(decisionForm);
    setDecisionErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      setSubmittingDecision(true);
      setError("");
      setSuccess("");

      await saveDecision({
        ticket_id: ticketId,
        ...decisionForm,
        review_comment: decisionForm.review_comment.trim(),
        reviewed_by: decisionForm.reviewed_by.trim(),
      });

      await loadTicketData();
      setActiveTab("review");
      setSuccess("Review decision saved successfully.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to save decision.");
    } finally {
      setSubmittingDecision(false);
    }
  }

  async function handleAssignmentSubmit(e) {
    e.preventDefault();

    const errors = validateAssignmentForm(assignmentForm);
    setAssignmentErrors(errors);
    if (Object.keys(errors).length > 0) return;

    try {
      setSubmittingAssignment(true);
      setError("");
      setSuccess("");

      await assignTicket({
        ticket_id: ticketId,
        ...assignmentForm,
        assigned_by: assignmentForm.assigned_by.trim(),
        assignment_note: assignmentForm.assignment_note.trim(),
      });

      await loadTicketData();
      setActiveTab("assignment");
      setSuccess("Ticket assigned successfully.");
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to assign ticket.");
    } finally {
      setSubmittingAssignment(false);
    }
  }

  function renderOverview() {
    return (
      <div className="detail-main">
        <SectionCard title="Ticket Details">
          <div className="details-grid">
            <LabelValue label="Ticket ID" value={ticket.ticket_id} />
            <LabelValue label="Title" value={ticket.title} />
            <div className="kv">
              <span className="kv-label">Status</span>
              <span className="kv-value">
                <Badge value={ticket.status} type="status" />
              </span>
            </div>
            <LabelValue label="Reporter" value={ticket.reporter} />
            <LabelValue label="Source" value={ticket.source} />
            <LabelValue label="Description" value={ticket.description} />
          </div>
        </SectionCard>

        <SectionCard title="Stored Outcome">
          <div className="details-grid">
            <LabelValue label="Final Category" value={ticket.decision?.final_category} />
            <LabelValue label="Final Priority" value={ticket.decision?.final_priority} />
            <LabelValue label="Final Team" value={ticket.decision?.final_team} />
            <LabelValue label="Reviewed By" value={ticket.decision?.reviewed_by} />
            <LabelValue label="Assigned Team" value={ticket.assignment?.assigned_team} />
            <LabelValue label="Assigned By" value={ticket.assignment?.assigned_by} />
            <LabelValue label="Assignment Note" value={ticket.assignment?.assignment_note} />
          </div>
        </SectionCard>
      </div>
    );
  }

  function renderAnalysis() {
    return (
      <SectionCard title="AI Analysis">
        {!ticket.analysis ? (
          <p>No analysis available.</p>
        ) : (
          <div className="details-grid">
            <div className="kv">
              <span className="kv-label">Predicted Category</span>
              <span className="kv-value">
                <Badge value={ticket.analysis.predicted_category} type="category" />
              </span>
            </div>
            <LabelValue label="Category Confidence" value={ticket.analysis.category_confidence} />
            <div className="kv">
              <span className="kv-label">Predicted Priority</span>
              <span className="kv-value">
                <Badge value={ticket.analysis.predicted_priority} type="priority" />
              </span>
            </div>
            <LabelValue label="Priority Confidence" value={ticket.analysis.priority_confidence} />
            <LabelValue label="Suggested Team" value={ticket.analysis.suggested_team} />
            <LabelValue label="Next Step" value={ticket.analysis.next_step} />
            <LabelValue label="Summary" value={ticket.analysis.summary} />
            <LabelValue label="Rationale" value={ticket.analysis.rationale} />
            <LabelValue label="Model Version" value={ticket.analysis.model_version} />
            <LabelValue label="Analyzed At" value={ticket.analysis.analyzed_at} />
          </div>
        )}
      </SectionCard>
    );
  }

  function renderReview() {
    return (
      <div className="detail-side">
        <SectionCard title="Review Decision">
          <form className="form" onSubmit={handleDecisionSubmit}>
            <label>
              Final Category
              <select
                value={decisionForm.final_category}
                onChange={(e) =>
                  setDecisionForm({ ...decisionForm, final_category: e.target.value })
                }
              >
                {CATEGORY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <FieldError message={decisionErrors.final_category} />
            </label>

            <label>
              Final Priority
              <select
                value={decisionForm.final_priority}
                onChange={(e) =>
                  setDecisionForm({ ...decisionForm, final_priority: e.target.value })
                }
              >
                {PRIORITY_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <FieldError message={decisionErrors.final_priority} />
            </label>

            <label>
              Final Team
              <select
                value={decisionForm.final_team}
                onChange={(e) =>
                  setDecisionForm({ ...decisionForm, final_team: e.target.value })
                }
              >
                {TEAM_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <FieldError message={decisionErrors.final_team} />
            </label>

            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={decisionForm.accepted_ai_suggestion}
                onChange={(e) =>
                  setDecisionForm({
                    ...decisionForm,
                    accepted_ai_suggestion: e.target.checked,
                  })
                }
              />
              Accepted AI Suggestion
            </label>

            <label>
              Review Comment
              <textarea
                rows="4"
                value={decisionForm.review_comment}
                onChange={(e) =>
                  setDecisionForm({ ...decisionForm, review_comment: e.target.value })
                }
                maxLength={1000}
              />
              <FieldError message={decisionErrors.review_comment} />
            </label>

            <label>
              Reviewed By
              <input
                value={decisionForm.reviewed_by}
                onChange={(e) =>
                  setDecisionForm({ ...decisionForm, reviewed_by: e.target.value })
                }
                maxLength={100}
              />
              <FieldError message={decisionErrors.reviewed_by} />
            </label>

            <button type="submit" disabled={submittingDecision || !decisionFormValid}>
              {submittingDecision ? "Saving..." : "Save Decision"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Current Review State">
          <div className="details-grid">
            <LabelValue label="Final Category" value={ticket.decision?.final_category} />
            <LabelValue label="Final Priority" value={ticket.decision?.final_priority} />
            <LabelValue label="Final Team" value={ticket.decision?.final_team} />
            <LabelValue label="Accepted AI Suggestion" value={String(ticket.decision?.accepted_ai_suggestion ?? "—")} />
            <LabelValue label="Review Comment" value={ticket.decision?.review_comment} />
            <LabelValue label="Reviewed By" value={ticket.decision?.reviewed_by} />
          </div>
        </SectionCard>
      </div>
    );
  }

  function renderAssignment() {
    return (
      <div className="detail-side">
        <SectionCard title="Assignment">
          <form className="form" onSubmit={handleAssignmentSubmit}>
            <label>
              Assigned Team
              <select
                value={assignmentForm.assigned_team}
                onChange={(e) =>
                  setAssignmentForm({ ...assignmentForm, assigned_team: e.target.value })
                }
              >
                {TEAM_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
              <FieldError message={assignmentErrors.assigned_team} />
            </label>

            <label>
              Assigned By
              <input
                value={assignmentForm.assigned_by}
                onChange={(e) =>
                  setAssignmentForm({ ...assignmentForm, assigned_by: e.target.value })
                }
                maxLength={100}
              />
              <FieldError message={assignmentErrors.assigned_by} />
            </label>

            <label>
              Assignment Note
              <textarea
                rows="4"
                value={assignmentForm.assignment_note}
                onChange={(e) =>
                  setAssignmentForm({ ...assignmentForm, assignment_note: e.target.value })
                }
                maxLength={1000}
              />
              <FieldError message={assignmentErrors.assignment_note} />
            </label>

            <button type="submit" disabled={submittingAssignment || !assignmentFormValid}>
              {submittingAssignment ? "Assigning..." : "Assign Ticket"}
            </button>
          </form>
        </SectionCard>

        <SectionCard title="Current Assignment State">
          <div className="details-grid">
            <LabelValue label="Assigned Team" value={ticket.assignment?.assigned_team} />
            <LabelValue label="Assigned By" value={ticket.assignment?.assigned_by} />
            <LabelValue label="Assignment Note" value={ticket.assignment?.assignment_note} />
          </div>
        </SectionCard>
      </div>
    );
  }

  function renderActiveTab() {
    if (!ticket) return null;

    if (activeTab === "overview") return renderOverview();
    if (activeTab === "analysis") return renderAnalysis();
    if (activeTab === "review") return renderReview();
    if (activeTab === "assignment") return renderAssignment();

    return renderOverview();
  }

  return (
    <div className="app-shell">
      <header className="page-header page-header-row">
        <div>
          <p className="eyebrow">Ticket Detail</p>
          <h1>Ticket Details</h1>
          <p className="subtitle">
            Review, validate and assign a single ticket.
          </p>
        </div>

        <Link className="secondary-button" to="/">
          ← Back to Dashboard
        </Link>
      </header>

      <MessageBanner type="error" message={error} />
      <MessageBanner type="success" message={success} />

      {loading ? (
        <SectionCard title="Loading">
          <p>Loading ticket...</p>
        </SectionCard>
      ) : !ticket ? (
        <SectionCard title="Not found">
          <p>Ticket could not be loaded.</p>
        </SectionCard>
      ) : (
        <>
          <SectionCard title="Action Bar">
            <div className="actionbar">
              <button
                type="button"
                className="quick-action-button"
                onClick={handleAcceptAiRecommendation}
                disabled={!ticket.analysis || runningQuickAction}
              >
                Accept AI Recommendation
              </button>

              <button
                type="button"
                className="quick-action-button"
                onClick={handleAssignToSuggestedTeam}
                disabled={!ticket.analysis?.suggested_team || runningQuickAction}
              >
                Assign to Suggested Team
              </button>

              <button
                type="button"
                className="quick-action-button secondary"
                onClick={applyAiToDecisionForm}
                disabled={!ticket.analysis}
              >
                Set Review Defaults from AI
              </button>

              <button
                type="button"
                className="quick-action-button secondary"
                onClick={copyAiTeamToAssignmentForm}
                disabled={!ticket.analysis?.suggested_team}
              >
                Copy AI Team to Assignment
              </button>
            </div>
          </SectionCard>

          <SectionCard title="Navigation">
            <div className="tabbar">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  type="button"
                  className={`tab-button ${activeTab === tab ? "active" : ""}`}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab === "overview" && "Overview"}
                  {tab === "analysis" && "AI Analysis"}
                  {tab === "review" && "Review"}
                  {tab === "assignment" && "Assignment"}
                </button>
              ))}
            </div>
          </SectionCard>

          {renderActiveTab()}
        </>
      )}
    </div>
  );
}
