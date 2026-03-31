import React from "react";

const LoadingState = ({
  title = "Loading data",
  message = "Please wait while the latest information is prepared.",
  rows = 3,
  compact = false,
}) => {
  const items = Array.from({ length: rows }, (_, index) => index);

  return (
    <section className={`state-card ${compact ? "state-card--compact" : ""}`} aria-busy="true">
      <div className="state-card__header">
        <div className="state-card__eyebrow">Loading</div>
        <h3 className="state-card__title">{title}</h3>
        <p className="state-card__message">{message}</p>
      </div>

      <div className="skeleton-grid">
        {items.map((item) => (
          <div key={item} className="skeleton-row">
            <div className="skeleton skeleton--title" />
            <div className="skeleton skeleton--text" />
            <div className="skeleton skeleton--text skeleton--short" />
          </div>
        ))}
      </div>
    </section>
  );
};

export default LoadingState;
