import ColumnVisibilityMenu from "./ColumnVisibilityMenu";

function translateFilterValue(value, type) {
  const normalized = String(value || "").toLowerCase();

  if (type === "status") {
    return {
      new: "Neu",
      triaged: "Triagiert",
      reviewed: "Geprüft",
      assigned: "Zugewiesen",
      closed: "Geschlossen",
    }[normalized] || value;
  }

  if (type === "priority") {
    return {
      low: "Niedrig",
      medium: "Mittel",
      high: "Hoch",
      critical: "Kritisch",
    }[normalized] || value;
  }

  if (type === "source") {
    return {
      internal: "Intern",
      external: "Extern",
    }[normalized] || value;
  }

  return value;
}

export default function TicketFilters({
  activeView,
  viewOptions,
  customViews,
  filters,
  facets,
  columns,
  visibleColumns,
  onViewChange,
  onApplyCustomView,
  onSaveCurrentView,
  onFilterChange,
  onResetFilters,
  onToggleColumn,
}) {
  return (
    <div className="ticket-filters-panel">
      <div className="ticket-filters-topline">
        <div>
          <span className="ticket-filters-eyebrow">Gespeicherte Sichten</span>
          <h3>Arbeite mit klaren Views statt mit Einzelfiltern</h3>
        </div>
        <div className="ticket-filters-actions">
          <button type="button" className="secondary-button workbench-inline-button" onClick={onSaveCurrentView}>
            Aktuelle Sicht speichern
          </button>
          <ColumnVisibilityMenu
            columns={columns}
            visibleColumns={visibleColumns}
            onToggleColumn={onToggleColumn}
          />
        </div>
      </div>

      <div className="saved-view-row">
        {viewOptions.map((view) => (
          <button
            key={view.key}
            type="button"
            className={`saved-view-chip ${activeView === view.key ? "active" : ""}`}
            onClick={() => onViewChange(view.key)}
          >
            {view.label}
          </button>
        ))}

        {customViews.map((view) => (
          <button
            key={view.id}
            type="button"
            className="saved-view-chip saved-view-chip-custom"
            onClick={() => onApplyCustomView(view.id)}
          >
            {view.label}
          </button>
        ))}
      </div>

      <div className="ticket-filter-grid">
        <label>
          Suche
          <input
            className="toolbar-input"
            value={filters.q}
            placeholder="Titel, Beschreibung, Ticket-ID oder Tags durchsuchen"
            onChange={(event) => onFilterChange("q", event.target.value)}
          />
        </label>

        <label>
          Status
          <select
            className="toolbar-select"
            value={filters.status}
            onChange={(event) => onFilterChange("status", event.target.value)}
          >
            <option value="all">Alle Status</option>
            {facets.statuses.map((value) => (
              <option key={value} value={value}>
                {translateFilterValue(value, "status")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Priorität
          <select
            className="toolbar-select"
            value={filters.priority}
            onChange={(event) => onFilterChange("priority", event.target.value)}
          >
            <option value="all">Alle Prioritäten</option>
            {facets.priorities.map((value) => (
              <option key={value} value={value}>
                {translateFilterValue(value, "priority")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Abteilung
          <select
            className="toolbar-select"
            value={filters.department}
            onChange={(event) => onFilterChange("department", event.target.value)}
          >
            <option value="all">Alle Abteilungen</option>
            {facets.departments.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        <label>
          Quelle
          <select
            className="toolbar-select"
            value={filters.source}
            onChange={(event) => onFilterChange("source", event.target.value)}
          >
            <option value="all">Alle Quellen</option>
            {facets.sources.map((value) => (
              <option key={value} value={value}>
                {translateFilterValue(value, "source")}
              </option>
            ))}
          </select>
        </label>

        <label>
          Sortierung
          <select
            className="toolbar-select"
            value={`${filters.sort_by}:${filters.sort_dir}`}
            onChange={(event) => {
              const [sortBy, sortDir] = event.target.value.split(":");
              onFilterChange({ sort_by: sortBy, sort_dir: sortDir });
            }}
          >
            <option value="updated_at:desc">Letzte Aktivität zuerst</option>
            <option value="created_at:desc">Neueste zuerst</option>
            <option value="priority:desc">Höchste Priorität zuerst</option>
            <option value="status:asc">Status A-Z</option>
            <option value="title:asc">Titel A-Z</option>
          </select>
        </label>
      </div>

      <div className="ticket-filters-footer">
        <p>
          Die Workbench nutzt die Listen-API mit Suche, Filtern, Pagination und den erweiterten Team-, Assignee- und
          SLA-Feldern.
        </p>
        <button type="button" className="secondary-button workbench-inline-button" onClick={onResetFilters}>
          Filter zurücksetzen
        </button>
      </div>
    </div>
  );
}
