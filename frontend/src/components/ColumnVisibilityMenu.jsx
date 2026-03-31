import { useMemo, useState } from "react";

export default function ColumnVisibilityMenu({ columns, visibleColumns, onToggleColumn }) {
  const [open, setOpen] = useState(false);

  const visibleCount = useMemo(
    () => visibleColumns.filter((columnKey) => columns.some((column) => column.key === columnKey)).length,
    [columns, visibleColumns]
  );

  return (
    <div className="column-visibility-menu">
      <button type="button" className="secondary-button workbench-inline-button" onClick={() => setOpen((current) => !current)}>
        Spalten
        <span className="workbench-inline-pill">{visibleCount}</span>
      </button>

      {open ? (
        <div className="column-visibility-panel">
          <div className="column-visibility-panel-header">
            <strong>Sichtbare Spalten</strong>
            <span>{visibleCount} aktiv</span>
          </div>

          <div className="column-visibility-options">
            {columns.map((column) => {
              const checked = visibleColumns.includes(column.key);
              const disabled = checked && visibleCount <= 1;

              return (
                <label key={column.key} className="column-visibility-option">
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => onToggleColumn(column.key)}
                  />
                  <span>{column.label}</span>
                </label>
              );
            })}
          </div>
        </div>
      ) : null}
    </div>
  );
}
