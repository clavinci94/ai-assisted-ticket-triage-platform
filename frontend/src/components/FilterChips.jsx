export default function FilterChips({ chips, onRemove, onClear }) {
  if (!chips.length) {
    return null;
  }

  return (
    <div className="filter-chip-row">
      {chips.map((chip) => (
        <button
          key={chip.key}
          type="button"
          className="filter-chip"
          onClick={() => onRemove(chip.key)}
        >
          <span>{chip.label}</span>
          <strong>×</strong>
        </button>
      ))}

      <button type="button" className="filter-chip filter-chip-clear" onClick={onClear}>
        Alle Filter entfernen
      </button>
    </div>
  );
}
