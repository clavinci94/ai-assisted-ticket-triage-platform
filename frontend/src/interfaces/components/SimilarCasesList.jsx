import { useNavigate } from "react-router-dom";

/**
 * Renders the "similar historical cases" panel that appears in the
 * AI-recommendation modal. Each row is clickable and takes the operator
 * to the referenced ticket so they can read the full context before
 * accepting or rejecting the recommendation.
 *
 * Designed to degrade gracefully: if no cases are passed in, the component
 * returns null — the caller never has to guard.
 *
 * Score badges are color-banded so operators can tell at a glance whether
 * a reference is a strong match (green) or a weaker but still above-floor
 * one (amber). The backend filter guarantees we never receive scores below
 * the minimum-similarity threshold.
 */
const STRONG_MATCH_THRESHOLD = 0.5;

function scoreTone(score) {
  return score >= STRONG_MATCH_THRESHOLD ? "strong" : "moderate";
}

function scoreLabel(tone) {
  return tone === "strong"
    ? "Starke Übereinstimmung"
    : "Mittlere Übereinstimmung — als Orientierung";
}

export default function SimilarCasesList({ cases, onNavigate }) {
  const navigate = useNavigate();

  if (!cases || cases.length === 0) {
    return null;
  }

  const handleOpen = (ticketId) => {
    if (typeof onNavigate === "function") {
      onNavigate(ticketId);
      return;
    }
    navigate(`/tickets/${ticketId}`);
  };

  return (
    <div className="similar-cases" aria-label="Ähnliche Fälle">
      <div className="similar-cases-header">
        <strong>Ähnliche Fälle aus der Historie</strong>
        <span className="similar-cases-hint">
          Aus reviewten Tickets — erklärt, warum die KI so routet.
        </span>
      </div>
      <ul className="similar-cases-list">
        {cases.map((item) => {
          const score = item.similarity_score || 0;
          const tone = scoreTone(score);
          return (
            <li key={item.ticket_id}>
              <button
                type="button"
                className="similar-case-row"
                onClick={() => handleOpen(item.ticket_id)}
                title={`Zum Ticket ${item.ticket_id} wechseln`}
              >
                <span
                  className={`similar-case-score similar-case-score-${tone}`}
                  title={scoreLabel(tone)}
                  aria-label={scoreLabel(tone)}
                >
                  {Math.round(score * 100)}%
                </span>
                <span className="similar-case-body">
                  <span className="similar-case-title">
                    #{item.ticket_id} · {item.title}
                  </span>
                  <span className="similar-case-meta">
                    <span>{item.final_department}</span>
                    {item.final_team ? <span>· {item.final_team}</span> : null}
                    <span>· {item.final_category}</span>
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
