export default function PaginationControls({
  page,
  totalPages,
  total,
  pageSize,
  onPageChange,
  onPageSizeChange,
}) {
  return (
    <div className="pagination-bar">
      <div className="pagination-copy">
        <strong>{total} Treffer</strong>
        <span>{page} / {totalPages} Seiten</span>
      </div>

      <div className="pagination-actions">
        <label className="pagination-size-select">
          <span>Pro Seite</span>
          <select value={pageSize} onChange={(event) => onPageSizeChange(Number(event.target.value))}>
            {[10, 20, 50].map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="secondary-button workbench-inline-button"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          Zurück
        </button>
        <button
          type="button"
          className="secondary-button workbench-inline-button"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
        >
          Weiter
        </button>
      </div>
    </div>
  );
}
