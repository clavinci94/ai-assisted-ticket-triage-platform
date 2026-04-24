import { NavLink } from "react-router-dom";

/**
 * Horizontal tab bar backed by react-router NavLinks, so the active state
 * reflects the current URL and bookmarks / browser-back keep working.
 *
 * Each `items` entry is `{ to, label, end? }` — same shape as NavLink's
 * props. `end` should be set for routes that would otherwise match their
 * children (e.g. `/tickets` matching `/tickets/mine`).
 */
export default function Tabs({ items, ariaLabel }) {
  return (
    <nav className="app-tabs" aria-label={ariaLabel}>
      {items.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={item.end}
          className={({ isActive }) => `app-tab ${isActive ? "active" : ""}`}
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  );
}
