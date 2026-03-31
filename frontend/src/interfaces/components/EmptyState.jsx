import React from "react";

const EmptyState = ({
  title = "Nothing to show yet",
  message = "Create or import data to populate this section.",
  action,
}) => {
  return (
    <section className="state-card state-card--empty" role="status" aria-live="polite">
      <div className="state-card__header">
        <div className="state-card__eyebrow">Empty</div>
        <h3 className="state-card__title">{title}</h3>
        <p className="state-card__message">{message}</p>
      </div>
      {action ? <div className="state-card__action">{action}</div> : null}
    </section>
  );
};

export default EmptyState;
