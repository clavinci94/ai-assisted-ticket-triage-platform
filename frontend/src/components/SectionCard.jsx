export default function SectionCard({ title, actions, children }) {
  return (
    <section className="card">
      <div className="card-header">
        <h2>{title}</h2>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  );
}
