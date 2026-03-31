export const WORKBENCH_OPERATOR_KEY = "ticket-workbench-operator";
export const USER_SETTINGS_KEY = "ticket-triage-settings";

export const DEFAULT_USER_SETTINGS = {
  operatorName: "claudio",
  dashboardWorkspace: "overview",
  reportsStartPage: "/reports",
};

export function loadUserSettings() {
  if (typeof window === "undefined") {
    return DEFAULT_USER_SETTINGS;
  }

  try {
    const raw = window.localStorage.getItem(USER_SETTINGS_KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return {
      ...DEFAULT_USER_SETTINGS,
      ...(parsed && typeof parsed === "object" ? parsed : {}),
      operatorName:
        parsed?.operatorName ||
        window.localStorage.getItem(WORKBENCH_OPERATOR_KEY) ||
        DEFAULT_USER_SETTINGS.operatorName,
    };
  } catch {
    return {
      ...DEFAULT_USER_SETTINGS,
      operatorName:
        window.localStorage.getItem(WORKBENCH_OPERATOR_KEY) ||
        DEFAULT_USER_SETTINGS.operatorName,
    };
  }
}

export function saveUserSettings(settings) {
  if (typeof window === "undefined") {
    return DEFAULT_USER_SETTINGS;
  }

  const nextSettings = {
    ...DEFAULT_USER_SETTINGS,
    ...settings,
  };

  window.localStorage.setItem(USER_SETTINGS_KEY, JSON.stringify(nextSettings));
  window.localStorage.setItem(WORKBENCH_OPERATOR_KEY, nextSettings.operatorName || DEFAULT_USER_SETTINGS.operatorName);
  window.dispatchEvent(new Event("ticket-triage-settings-updated"));
  return nextSettings;
}

export function getOperatorName() {
  return loadUserSettings().operatorName || DEFAULT_USER_SETTINGS.operatorName;
}

export function getOperatorInitials() {
  const value = getOperatorName().trim();
  if (!value) {
    return "OP";
  }

  const segments = value.split(/\s+/).filter(Boolean);
  return segments.slice(0, 2).map((segment) => segment[0]?.toUpperCase() || "").join("") || "OP";
}
