export default function LabelValue({ label, value }) {
  return (
    <div className="kv">
      <span className="kv-label">{label}</span>
      <span className="kv-value">{value ?? "—"}</span>
    </div>
  );
}
