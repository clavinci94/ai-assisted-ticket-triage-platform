import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useToast } from "../components/ToastProvider";
import SectionCard from "../components/SectionCard";
import { previewTriageTicket, triageTicket } from "../lib/api";
import { DEPARTMENTS } from "../lib/departments";

const CATEGORY_OPTIONS = [
  { value: "", label: "Keine Vorgabe" },
  { value: "bug", label: "Fehler" },
  { value: "feature", label: "Funktion" },
  { value: "support", label: "Support" },
  { value: "requirement", label: "Anforderung" },
  { value: "question", label: "Frage" },
];

const PRIORITY_OPTIONS = [
  { value: "", label: "Keine Vorgabe" },
  { value: "low", label: "Niedrig" },
  { value: "medium", label: "Mittel" },
  { value: "high", label: "Hoch" },
  { value: "critical", label: "Kritisch" },
];

const initialTicketForm = {
  title: "",
  description: "",
  reporter: "",
  source: "internal",
  category: "",
  priority: "",
  team: "",
  assignee: "",
  due_at: "",
  tags_input: "",
};

function buildTicketPayload(form) {
  return {
    title: form.title,
    description: form.description,
    reporter: form.reporter || null,
    source: form.source,
    category: form.category || null,
    priority: form.priority || null,
    team: form.team || null,
    assignee: form.assignee || null,
    due_at: form.due_at || null,
    tags: form.tags_input
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
  };
}

export default function DashboardCreatePage() {
  const navigate = useNavigate();
  const { showToast } = useToast();

  const [ticketForm, setTicketForm] = useState(initialTicketForm);
  const [submitting, setSubmitting] = useState(false);
  const [previewAnalysis, setPreviewAnalysis] = useState(null);
  const [showRecommendationModal, setShowRecommendationModal] = useState(false);
  const [manualDepartmentMode, setManualDepartmentMode] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState(DEPARTMENTS[0]);

  const handleTriageSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);

    try {
      const preview = await previewTriageTicket(buildTicketPayload(ticketForm));
      setPreviewAnalysis(preview);
      setSelectedDepartment(preview.suggested_department || DEPARTMENTS[0]);
      setManualDepartmentMode(false);
      setShowRecommendationModal(true);
    } catch (error) {
      showToast({
        type: "error",
        title: "Erstellung fehlgeschlagen",
        message: error?.response?.data?.detail || "Die KI-Empfehlung konnte nicht geladen werden.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcceptRecommendation = async () => {
    if (!previewAnalysis) {
      return;
    }

    setSubmitting(true);

    try {
      const result = await triageTicket({
        ...buildTicketPayload(ticketForm),
        department: previewAnalysis.suggested_department,
        department_locked: false,
      });
      showToast({
        type: "success",
        title: "Ticket erstellt",
        message: `Das Ticket wurde in ${previewAnalysis.suggested_department} triagiert.`,
      });
      setShowRecommendationModal(false);
      navigate(`/tickets/${result.ticket_id}`);
    } catch (error) {
      showToast({
        type: "error",
        title: "Speichern fehlgeschlagen",
        message: error?.response?.data?.detail || "Das Ticket konnte nicht angelegt werden.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleSaveWithManualDepartment = async () => {
    setSubmitting(true);

    try {
      const result = await triageTicket({
        ...buildTicketPayload(ticketForm),
        department: selectedDepartment,
        department_locked: true,
      });
      showToast({
        type: "success",
        title: "Ticket erstellt",
        message: `Das Ticket wurde in ${selectedDepartment} gespeichert.`,
      });
      setShowRecommendationModal(false);
      navigate(`/tickets/${result.ticket_id}`);
    } catch (error) {
      showToast({
        type: "error",
        title: "Speichern fehlgeschlagen",
        message: error?.response?.data?.detail || "Das Ticket konnte nicht angelegt werden.",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const closeRecommendationModal = () => {
    if (submitting) {
      return;
    }
    setShowRecommendationModal(false);
    setManualDepartmentMode(false);
  };

  return (
    <div className="app-shell dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Ticket-Erstellung</p>
          <h1>Neues Ticket erstellen</h1>
          <p className="subtitle">
            Erfasse die wichtigsten Details und lasse die KI den ersten Routing-Vorschlag für dich
            vorbereiten.
          </p>
        </div>
      </section>

      <section className="dashboard-layout-page">
        <div className="left-column">
          <SectionCard title="Ticket erfassen & triagieren">
            <form className="form" onSubmit={handleTriageSubmit}>
              <label>
                Titel
                <input
                  value={ticketForm.title}
                  onChange={(e) => setTicketForm({ ...ticketForm, title: e.target.value })}
                  required
                />
              </label>

              <label>
                Beschreibung
                <textarea
                  rows="5"
                  value={ticketForm.description}
                  onChange={(e) => setTicketForm({ ...ticketForm, description: e.target.value })}
                  required
                />
              </label>

              <label>
                Reporter
                <input
                  value={ticketForm.reporter}
                  onChange={(e) => setTicketForm({ ...ticketForm, reporter: e.target.value })}
                />
              </label>

              <label>
                Kategorie
                <select
                  value={ticketForm.category}
                  onChange={(event) => setTicketForm({ ...ticketForm, category: event.target.value })}
                >
                  {CATEGORY_OPTIONS.map((option) => (
                    <option key={option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Priorität
                <select
                  value={ticketForm.priority}
                  onChange={(event) => setTicketForm({ ...ticketForm, priority: event.target.value })}
                >
                  {PRIORITY_OPTIONS.map((option) => (
                    <option key={option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Teamkontext
                <input
                  value={ticketForm.team}
                  onChange={(event) => setTicketForm({ ...ticketForm, team: event.target.value })}
                  placeholder="z. B. Payments Operations Squad"
                />
              </label>

              <label>
                Zuständige Person
                <input
                  value={ticketForm.assignee}
                  onChange={(event) => setTicketForm({ ...ticketForm, assignee: event.target.value })}
                  placeholder="z. B. claudio"
                />
              </label>

              <label>
                Fälligkeitsdatum
                <input
                  type="datetime-local"
                  value={ticketForm.due_at}
                  onChange={(event) => setTicketForm({ ...ticketForm, due_at: event.target.value })}
                />
              </label>

              <label>
                Tags
                <input
                  value={ticketForm.tags_input}
                  onChange={(event) => setTicketForm({ ...ticketForm, tags_input: event.target.value })}
                  placeholder="z. B. Kunde, Mobile App, SLA"
                />
              </label>

              <div className="form-hint-block">
                <strong>Zuständige Abteilung</strong>
                <p>
                  Wird während der KI-Triage automatisch empfohlen und direkt am Ticket
                  hinterlegt.
                </p>
              </div>

              <label>
                Quelle
                <select
                  value={ticketForm.source}
                  onChange={(e) => setTicketForm({ ...ticketForm, source: e.target.value })}
                >
                  <option value="internal">Intern</option>
                  <option value="external">Extern</option>
                </select>
              </label>

              <button className="primary-button" type="submit" disabled={submitting}>
                {submitting ? "Prüfe Empfehlung..." : "Ticket triagieren"}
              </button>
            </form>
          </SectionCard>
        </div>

        <div className="right-column">
          <SectionCard title="Was passiert als Nächstes?">
            <p>
              Das neue Ticket wird in den Triage-Prozess eingespeist und erhält eine
              Kategorie, Priorität, zuständige Abteilung und Teamempfehlung.
            </p>
            <p>
              Zusätzliche Metadaten wie Tags, Fälligkeit, Teamkontext oder zuständige Person
              bleiben am Ticket erhalten und stehen danach auch in Workbench und Detailansicht zur Verfügung.
            </p>
            <button className="secondary-button" type="button" onClick={() => navigate("/dashboard")}>
              Zurück zum Dashboard
            </button>
          </SectionCard>
        </div>
      </section>

      {showRecommendationModal && previewAnalysis ? (
        <div className="modal-backdrop" role="presentation">
          <div className="modal-card" role="dialog" aria-modal="true" aria-labelledby="department-recommendation-title">
            <p className="eyebrow">KI-Empfehlung</p>
            <h2 id="department-recommendation-title">Abteilung vor dem Speichern bestätigen</h2>
            <p>
              Die KI empfiehlt, dieses Ticket in <strong>{previewAnalysis.suggested_department}</strong> zu speichern.
            </p>
            <div className="modal-recommendation-box">
              <p><strong>Begründung</strong></p>
              <p>{previewAnalysis.rationale}</p>
            </div>
            <div className="modal-recommendation-meta">
              <span>Kategorie: {previewAnalysis.predicted_category}</span>
              <span>Priorität: {previewAnalysis.predicted_priority}</span>
              <span>Team: {previewAnalysis.suggested_team}</span>
            </div>

            {manualDepartmentMode ? (
              <label className="modal-select-label">
                Abteilung selbst auswählen
                <select
                  value={selectedDepartment}
                  onChange={(event) => setSelectedDepartment(event.target.value)}
                >
                  {DEPARTMENTS.map((department) => (
                    <option key={department} value={department}>
                      {department}
                    </option>
                  ))}
                </select>
              </label>
            ) : null}

            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={closeRecommendationModal} disabled={submitting}>
                Abbrechen
              </button>

              {manualDepartmentMode ? (
                <button type="button" className="primary-button" onClick={handleSaveWithManualDepartment} disabled={submitting}>
                  {submitting ? "Speichere..." : "Mit Auswahl speichern"}
                </button>
              ) : (
                <>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => setManualDepartmentMode(true)}
                    disabled={submitting}
                  >
                    Empfehlung ablehnen
                  </button>
                  <button type="button" className="primary-button" onClick={handleAcceptRecommendation} disabled={submitting}>
                    {submitting ? "Speichere..." : "Empfehlung akzeptieren"}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
