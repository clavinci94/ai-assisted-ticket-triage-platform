export default function AssigneePicker({
  team,
  assignee,
  note,
  submitting = false,
  onChange,
  onSubmit,
}) {
  return (
    <form className="detail-form" onSubmit={onSubmit}>
      <label className="detail-form-field">
        <span>Zuständiges Team</span>
        <input
          type="text"
          placeholder="z. B. payments-operations-team"
          value={team}
          onChange={(event) => onChange("team", event.target.value)}
          disabled={submitting}
        />
      </label>

      <label className="detail-form-field">
        <span>Bearbeitung</span>
        <input
          type="text"
          placeholder="z. B. claudio"
          value={assignee}
          onChange={(event) => onChange("assignee", event.target.value)}
          disabled={submitting}
        />
      </label>

      <label className="detail-form-field">
        <span>Zuweisungsnotiz</span>
        <textarea
          rows="4"
          placeholder="Warum wird dieses Ticket neu zugewiesen?"
          value={note}
          onChange={(event) => onChange("note", event.target.value)}
          disabled={submitting}
        />
      </label>

      <div className="detail-action-row">
        <button className="primary-button" type="submit" disabled={submitting || !team.trim()}>
          {submitting ? "Speichere Zuweisung..." : "Neu zuweisen"}
        </button>
      </div>
    </form>
  );
}
