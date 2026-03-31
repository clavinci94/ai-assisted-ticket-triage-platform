function buildSlaState({ dueAt, breached }) {
  if (breached) {
    return {
      label: "SLA verletzt",
      className: "sla-badge is-danger",
    };
  }

  if (!dueAt) {
    return {
      label: "Keine SLA-Frist",
      className: "sla-badge",
    };
  }

  const dueDate = new Date(dueAt);
  if (Number.isNaN(dueDate.getTime())) {
    return {
      label: "SLA unklar",
      className: "sla-badge",
    };
  }

  const diff = dueDate.getTime() - Date.now();
  if (diff <= 0) {
    return {
      label: "Frist überschritten",
      className: "sla-badge is-danger",
    };
  }

  if (diff <= 24 * 60 * 60 * 1000) {
    return {
      label: "Fällig in < 24h",
      className: "sla-badge is-warning",
    };
  }

  return {
    label: "Im SLA",
    className: "sla-badge is-success",
  };
}

export default function SlaBadge({ dueAt, breached = false }) {
  const state = buildSlaState({ dueAt, breached });
  return <span className={state.className}>{state.label}</span>;
}
