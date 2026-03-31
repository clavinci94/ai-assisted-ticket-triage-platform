import { useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import TicketList from "../components/TicketList";
import TicketFilters from "../components/TicketFilters";
import FilterChips from "../components/FilterChips";
import BulkActionsBar from "../components/BulkActionsBar";
import PaginationControls from "../components/PaginationControls";
import { useToast } from "../components/ToastProvider";
import { fetchTicketWorkbench } from "../../infrastructure/http/api";
import {
  buildDefaultWorkbenchFilters,
  COLUMN_OPTIONS,
  COLUMN_VISIBILITY_STORAGE_KEY,
  DEFAULT_VISIBLE_COLUMNS,
  getCurrentOperator,
  getWorkbenchView,
  loadStoredJson,
  persistJson,
  SAVED_VIEWS_STORAGE_KEY,
  WORKBENCH_VIEWS,
} from "../../application/tickets/ticketWorkbench";

const EMPTY_FACETS = {
  statuses: [],
  priorities: [],
  departments: [],
  sources: [],
};

const DEFAULT_LIST_RESPONSE = {
  items: [],
  total: 0,
  page: 1,
  page_size: 10,
  total_pages: 1,
  facets: EMPTY_FACETS,
};

function getFiltersFromSearchParams(searchParams) {
  const defaults = buildDefaultWorkbenchFilters();

  return {
    q: searchParams.get("q") || defaults.q,
    status: searchParams.get("status") || defaults.status,
    priority: searchParams.get("priority") || defaults.priority,
    department: searchParams.get("department") || defaults.department,
    source: searchParams.get("source") || defaults.source,
    sort_by: searchParams.get("sort_by") || defaults.sort_by,
    sort_dir: searchParams.get("sort_dir") || defaults.sort_dir,
    page: Number(searchParams.get("page") || defaults.page),
    page_size: Number(searchParams.get("page_size") || defaults.page_size),
  };
}

export default function TicketsPage({ initialView = "all" }) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { showToast } = useToast();

  const [workbenchData, setWorkbenchData] = useState(DEFAULT_LIST_RESPONSE);
  const [loading, setLoading] = useState(false);
  const [selectedTicketIds, setSelectedTicketIds] = useState([]);
  const [savedViews, setSavedViews] = useState(() => loadStoredJson(SAVED_VIEWS_STORAGE_KEY, []));
  const [visibleColumns, setVisibleColumns] = useState(() => {
    const storedColumns = loadStoredJson(COLUMN_VISIBILITY_STORAGE_KEY, DEFAULT_VISIBLE_COLUMNS);
    return Array.isArray(storedColumns) && storedColumns.length ? storedColumns : DEFAULT_VISIBLE_COLUMNS;
  });

  const activeView = getWorkbenchView(initialView);
  const filters = useMemo(() => getFiltersFromSearchParams(searchParams), [searchParams]);

  useEffect(() => {
    persistJson(SAVED_VIEWS_STORAGE_KEY, savedViews);
  }, [savedViews]);

  useEffect(() => {
    persistJson(COLUMN_VISIBILITY_STORAGE_KEY, visibleColumns);
  }, [visibleColumns]);

  useEffect(() => {
    async function loadWorkbench() {
      try {
        setLoading(true);

        const response = await fetchTicketWorkbench({
          q: filters.q || undefined,
          view: activeView.key,
          status: filters.status !== "all" ? filters.status : undefined,
          priority: filters.priority !== "all" ? filters.priority : undefined,
          department: filters.department !== "all" ? filters.department : undefined,
          source: filters.source !== "all" ? filters.source : undefined,
          sort_by: filters.sort_by,
          sort_dir: filters.sort_dir,
          page: filters.page,
          page_size: filters.page_size,
          operator: getCurrentOperator(),
        });

        setWorkbenchData(response);
      } catch (error) {
        showToast({
          type: "error",
          title: "Workbench konnte nicht geladen werden",
          message: error?.response?.data?.detail || "Die Ticketliste ist momentan nicht verfügbar.",
        });
      } finally {
        setLoading(false);
      }
    }

    loadWorkbench();
  }, [activeView.key, filters, showToast]);

  const activeChips = useMemo(() => {
    const chips = [];

    if (filters.q) {
      chips.push({ key: "q", label: `Suche: ${filters.q}` });
    }
    if (filters.status !== "all") {
      chips.push({ key: "status", label: `Status: ${filters.status}` });
    }
    if (filters.priority !== "all") {
      chips.push({ key: "priority", label: `Priorität: ${filters.priority}` });
    }
    if (filters.department !== "all") {
      chips.push({ key: "department", label: `Abteilung: ${filters.department}` });
    }
    if (filters.source !== "all") {
      chips.push({ key: "source", label: `Quelle: ${filters.source}` });
    }

    return chips;
  }, [filters]);

  function updateSearchParams(updates, { resetPage = true } = {}) {
    const defaults = buildDefaultWorkbenchFilters();
    const nextParams = new URLSearchParams(searchParams);

    Object.entries(updates).forEach(([key, value]) => {
      const normalizedValue = value == null ? "" : String(value);
      const defaultValue = String(defaults[key] ?? "");

      if (!normalizedValue || normalizedValue === defaultValue || normalizedValue === "all") {
        nextParams.delete(key);
      } else {
        nextParams.set(key, normalizedValue);
      }
    });

    if (resetPage && !Object.prototype.hasOwnProperty.call(updates, "page")) {
      nextParams.delete("page");
    }

    setSearchParams(nextParams, { replace: true });
  }

  function handleFilterChange(key, value) {
    if (typeof key === "object" && key !== null) {
      updateSearchParams(key);
      return;
    }

    updateSearchParams({ [key]: value });
  }

  function handleSort(columnKey) {
    const nextDir =
      filters.sort_by === columnKey && filters.sort_dir === "desc"
        ? "asc"
        : "desc";

    updateSearchParams({
      sort_by: columnKey,
      sort_dir: nextDir,
    });
  }

  function handleViewChange(viewKey) {
    navigate(getWorkbenchView(viewKey).path);
  }

  function handleResetFilters() {
    setSearchParams(new URLSearchParams(), { replace: true });
  }

  function handleRemoveChip(key) {
    const defaults = buildDefaultWorkbenchFilters();
    updateSearchParams({ [key]: defaults[key] ?? "" });
  }

  function handleToggleColumn(columnKey) {
    setVisibleColumns((currentColumns) => {
      if (currentColumns.includes(columnKey)) {
        if (currentColumns.length === 1) {
          return currentColumns;
        }

        return currentColumns.filter((value) => value !== columnKey);
      }

      const ordered = COLUMN_OPTIONS
        .map((column) => column.key)
        .filter((key) => key === columnKey || currentColumns.includes(key));

      return ordered;
    });
  }

  function handlePageChange(nextPage) {
    updateSearchParams({ page: nextPage }, { resetPage: false });
  }

  function handlePageSizeChange(nextPageSize) {
    updateSearchParams({ page_size: nextPageSize, page: 1 }, { resetPage: false });
  }

  function handleToggleSelect(ticketId) {
    setSelectedTicketIds((currentIds) =>
      currentIds.includes(ticketId)
        ? currentIds.filter((currentId) => currentId !== ticketId)
        : [...currentIds, ticketId]
    );
  }

  function handleToggleSelectAll(pageItems) {
    const pageIds = pageItems.map((item) => item.ticket_id);
    const allPageSelected = pageIds.every((ticketId) => selectedTicketIds.includes(ticketId));

    if (allPageSelected) {
      setSelectedTicketIds((currentIds) => currentIds.filter((ticketId) => !pageIds.includes(ticketId)));
      return;
    }

    setSelectedTicketIds((currentIds) => Array.from(new Set([...currentIds, ...pageIds])));
  }

  async function handleCopyIds() {
    if (!selectedTicketIds.length) {
      return;
    }

    try {
      await navigator.clipboard.writeText(selectedTicketIds.join(", "));
      showToast({
        type: "success",
        title: "IDs kopiert",
        message: `${selectedTicketIds.length} Ticket-IDs wurden in die Zwischenablage kopiert.`,
      });
    } catch {
      showToast({
        type: "error",
        title: "Kopieren fehlgeschlagen",
        message: "Die IDs konnten nicht in die Zwischenablage übernommen werden.",
      });
    }
  }

  function handleOpenFirstSelected() {
    if (!selectedTicketIds.length) {
      return;
    }

    navigate(`/tickets/${selectedTicketIds[0]}`);
  }

  function handleSaveCurrentView() {
    const label = window.prompt("Name für diese Sicht");

    if (!label) {
      return;
    }

    const savedView = {
      id: `view-${Date.now()}`,
      label,
      view: activeView.key,
      filters,
    };

    setSavedViews((currentViews) => [...currentViews, savedView]);
    showToast({
      type: "success",
      title: "Sicht gespeichert",
      message: `Die Sicht "${label}" steht jetzt in deiner Workbench zur Verfügung.`,
    });
  }

  function handleApplyCustomView(viewId) {
    const viewConfig = savedViews.find((item) => item.id === viewId);

    if (!viewConfig) {
      return;
    }

    const nextParams = new URLSearchParams();

    Object.entries(viewConfig.filters).forEach(([key, value]) => {
      if (!value || value === "all") {
        return;
      }
      nextParams.set(key, String(value));
    });

    navigate(`${getWorkbenchView(viewConfig.view).path}?${nextParams.toString()}`);
  }

  return (
    <div className="app-shell dashboard-shell">
      <section className="dashboard-hero">
        <div className="dashboard-hero-copy">
          <p className="eyebrow">Ticket-Workbench</p>
          <h1>{activeView.label}</h1>
          <p className="subtitle">{activeView.description}</p>
          <div className="hero-guide">
            <p>
              Diese Seite bündelt Suche, Mehrfachfilter, gespeicherte Sichten, Pagination und Bulk-Aktionen in einer
              echten Arbeitsansicht für den operativen Ticketbestand.
            </p>
          </div>
        </div>

        <div className="hero-summary-card">
          <span className="hero-summary-label">Treffer in Sicht</span>
          <strong className="hero-summary-value">{workbenchData.total}</strong>
          <span className="hero-summary-text">Aktuelle Anzahl Tickets in der gewählten Workbench-Ansicht</span>
        </div>
      </section>

      <section className="dashboard-pathbar">
        <div className="dashboard-breadcrumbs">
          <span>Tickets</span>
          <span>•</span>
          <span>{activeView.label}</span>
        </div>
        <div className="dashboard-actions">
          <button type="button" onClick={() => navigate("/dashboard")}>Dashboard</button>
          <button type="button" onClick={() => navigate("/dashboard/create")}>Ticket erfassen</button>
          <button type="button" onClick={() => navigate("/dashboard/kpis")}>KPIs</button>
        </div>
      </section>

      <TicketFilters
        activeView={activeView.key}
        viewOptions={Object.values(WORKBENCH_VIEWS)}
        customViews={savedViews}
        filters={filters}
        facets={workbenchData.facets || EMPTY_FACETS}
        columns={COLUMN_OPTIONS}
        visibleColumns={visibleColumns}
        onViewChange={handleViewChange}
        onApplyCustomView={handleApplyCustomView}
        onSaveCurrentView={handleSaveCurrentView}
        onFilterChange={handleFilterChange}
        onResetFilters={handleResetFilters}
        onToggleColumn={handleToggleColumn}
      />

      <FilterChips chips={activeChips} onRemove={handleRemoveChip} onClear={handleResetFilters} />

      <BulkActionsBar
        selectedCount={selectedTicketIds.length}
        onCopyIds={handleCopyIds}
        onOpenFirst={handleOpenFirstSelected}
        onClearSelection={() => setSelectedTicketIds([])}
      />

      <section className="workbench-table-card">
        <div className="workbench-table-header">
          <div>
            <span className="workbench-table-eyebrow">Operative Tabelle</span>
            <h2>{activeView.label}</h2>
            <p>Sortiere nach Spalten, markiere Zeilen und arbeite mit gespeicherten oder freien Filterkombinationen.</p>
          </div>
        </div>

        <TicketList
          variant="table"
          tickets={workbenchData.items}
          loading={loading}
          visibleColumns={visibleColumns}
          selectedTicketIds={selectedTicketIds}
          onToggleSelect={handleToggleSelect}
          onToggleSelectAll={handleToggleSelectAll}
          onSort={handleSort}
          sortBy={filters.sort_by}
          sortDir={filters.sort_dir}
        />

        <PaginationControls
          page={workbenchData.page}
          totalPages={workbenchData.total_pages}
          total={workbenchData.total}
          pageSize={workbenchData.page_size}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      </section>
    </div>
  );
}
