/**
 * Thin inline SVG icon set — no external dependency, no webfont.
 * All icons share the same viewBox, stroke-based style, and currentColor
 * inheritance, so they adapt to the context (sidebar vs. buttons) without
 * any per-component theming.
 */

const BASE_PROPS = {
  width: 16,
  height: 16,
  viewBox: "0 0 20 20",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.6,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
};

function withProps(props) {
  return { ...BASE_PROPS, ...props };
}

export function HomeIcon(props) {
  return (
    <svg {...withProps(props)}>
      <path d="M3.5 9 10 3.5 16.5 9v7a1 1 0 0 1-1 1H12v-5H8v5H4.5a1 1 0 0 1-1-1V9Z" />
    </svg>
  );
}

export function ListIcon(props) {
  return (
    <svg {...withProps(props)}>
      <path d="M7 5h10M7 10h10M7 15h10" />
      <circle cx="3.5" cy="5" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="3.5" cy="10" r="0.8" fill="currentColor" stroke="none" />
      <circle cx="3.5" cy="15" r="0.8" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ChartIcon(props) {
  return (
    <svg {...withProps(props)}>
      <path d="M3 17h14" />
      <path d="M6 13v3M10 8v8M14 10v6" />
    </svg>
  );
}

export function GearIcon(props) {
  return (
    <svg {...withProps(props)}>
      <circle cx="10" cy="10" r="2.5" />
      <path d="M10 2.5v2M10 15.5v2M3.6 3.6l1.4 1.4M15 15l1.4 1.4M2.5 10h2M15.5 10h2M3.6 16.4 5 15M15 5l1.4-1.4" />
    </svg>
  );
}

export function PlusIcon(props) {
  return (
    <svg {...withProps(props)}>
      <path d="M10 4v12M4 10h12" />
    </svg>
  );
}

export function QuestionIcon(props) {
  return (
    <svg {...withProps(props)}>
      <circle cx="10" cy="10" r="7.5" />
      <path d="M7.8 8a2.2 2.2 0 1 1 3 2.1c-.6.2-.8.5-.8 1v.4" />
      <circle cx="10" cy="13.8" r="0.6" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function SearchIcon(props) {
  return (
    <svg {...withProps(props)}>
      <circle cx="9" cy="9" r="5" />
      <path d="m13 13 4 4" />
    </svg>
  );
}
