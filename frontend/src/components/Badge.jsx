export default function Badge({ value, type = "default" }) {
  const normalized = String(value || "").toLowerCase();
  const translatedValue = translateBadgeValue(value, type);

  let className = "badge";

  if (type === "status") {
    if (normalized === "new") className += " badge-neutral";
    else if (normalized === "triaged") className += " badge-info";
    else if (normalized === "reviewed") className += " badge-warning";
    else if (normalized === "assigned") className += " badge-success";
  }

  if (type === "priority") {
    if (normalized === "low") className += " badge-neutral";
    else if (normalized === "medium") className += " badge-info";
    else if (normalized === "high") className += " badge-warning";
    else if (normalized === "critical") className += " badge-danger";
  }

  if (type === "category") {
    className += " badge-category";
  }

  return <span className={className}>{translatedValue}</span>;
}

function translateBadgeValue(value, type) {
  const normalized = String(value || "").toLowerCase();

  if (type === "status") {
    return (
      {
        new: "Neu",
        triaged: "Triagiert",
        reviewed: "Geprüft",
        assigned: "Zugewiesen",
      }[normalized] || value
    );
  }

  if (type === "priority") {
    return (
      {
        low: "Niedrig",
        medium: "Mittel",
        high: "Hoch",
        critical: "Kritisch",
      }[normalized] || value
    );
  }

  if (type === "category") {
    return (
      {
        bug: "Fehler",
        feature: "Funktion",
        support: "Support",
        requirement: "Anforderung",
        question: "Frage",
        unknown: "Unbekannt",
      }[normalized] || value
    );
  }

  return value;
}
