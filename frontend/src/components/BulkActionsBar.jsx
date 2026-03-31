export default function BulkActionsBar({
  selectedCount,
  onCopyIds,
  onOpenFirst,
  onClearSelection,
}) {
  if (!selectedCount) {
    return null;
  }

  return (
    <div className="bulk-actions-bar">
      <div className="bulk-actions-copy">
        <span className="bulk-actions-label">Auswahl aktiv</span>
        <strong>{selectedCount} Tickets markiert</strong>
      </div>

      <div className="bulk-actions-buttons">
        <button type="button" className="secondary-button workbench-inline-button" onClick={onCopyIds}>
          IDs kopieren
        </button>
        <button type="button" className="secondary-button workbench-inline-button" onClick={onOpenFirst}>
          Erstes Ticket öffnen
        </button>
        <button type="button" className="secondary-button workbench-inline-button" onClick={onClearSelection}>
          Auswahl leeren
        </button>
      </div>
    </div>
  );
}
