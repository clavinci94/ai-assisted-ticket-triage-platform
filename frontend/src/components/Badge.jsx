export default function Badge({ value, type = "default" }) {
  const normalized = String(value || "").toLowerCase();

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

  return <span className={className}>{value}</span>;
}
