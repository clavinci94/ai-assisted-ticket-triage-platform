import { useEffect, useState } from "react";

export default function CommentComposer({ onSubmit, submitting = false, defaultActor = "claudio" }) {
  const [form, setForm] = useState({
    actor: defaultActor,
    body: "",
    isInternal: false,
  });

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- syncing an externally changed default (operator settings) into a locally-editable form field.
    setForm((current) => ({ ...current, actor: current.actor || defaultActor }));
  }, [defaultActor]);

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.body.trim()) {
      return;
    }

    const shouldReset = await onSubmit?.({
      actor: form.actor.trim() || null,
      body: form.body.trim(),
      isInternal: form.isInternal,
    });

    if (shouldReset !== false) {
      setForm((current) => ({
        actor: current.actor,
        body: "",
        isInternal: false,
      }));
    }
  }

  return (
    <form className="comment-composer" onSubmit={handleSubmit}>
      <div className="comment-composer-grid">
        <label className="detail-form-field">
          <span>Autor</span>
          <input
            type="text"
            value={form.actor}
            onChange={(event) => setForm({ ...form, actor: event.target.value })}
            disabled={submitting}
          />
        </label>

        <label className="comment-composer-toggle">
          <input
            type="checkbox"
            checked={form.isInternal}
            onChange={(event) => setForm({ ...form, isInternal: event.target.checked })}
            disabled={submitting}
          />
          <span>Als interne Notiz speichern</span>
        </label>
      </div>

      <label className="detail-form-field">
        <span>{form.isInternal ? "Interne Notiz" : "Kommentar"}</span>
        <textarea
          rows="4"
          placeholder="Kontext, Rückfrage oder operative Notiz ergänzen..."
          value={form.body}
          onChange={(event) => setForm({ ...form, body: event.target.value })}
          disabled={submitting}
        />
      </label>

      <div className="detail-action-row">
        <button className="primary-button" type="submit" disabled={submitting || !form.body.trim()}>
          {submitting ? "Speichere..." : form.isInternal ? "Interne Notiz speichern" : "Kommentar speichern"}
        </button>
      </div>
    </form>
  );
}
