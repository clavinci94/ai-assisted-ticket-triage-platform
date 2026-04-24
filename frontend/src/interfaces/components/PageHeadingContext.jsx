import { createContext, useContext, useEffect, useMemo, useState } from "react";

/**
 * Lightweight channel for pages to advertise their topbar title and an
 * optional inline count ("Tickets 33"). Avoids a global store; the
 * provider lives at the app shell root and pages push updates via
 * useSetPageHeading.
 */
const PageHeadingContext = createContext({
  heading: { title: "", count: null },
  setHeading: () => {},
});

export function PageHeadingProvider({ children }) {
  const [heading, setHeading] = useState({ title: "", count: null });
  const value = useMemo(() => ({ heading, setHeading }), [heading]);
  return <PageHeadingContext.Provider value={value}>{children}</PageHeadingContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components -- hooks ship alongside the provider by design.
export function usePageHeading() {
  return useContext(PageHeadingContext);
}

// eslint-disable-next-line react-refresh/only-export-components -- hooks ship alongside the provider by design.
export function useSetPageHeading(title, count = null) {
  const { setHeading } = useContext(PageHeadingContext);
  useEffect(() => {
    setHeading({ title, count });
  }, [title, count, setHeading]);
}
