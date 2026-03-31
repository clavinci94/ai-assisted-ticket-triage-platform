export const DEPARTMENTS = [
  "Bank-IT Support",
  "Retail Banking",
  "Corporate Banking",
  "Risk & Compliance",
  "Payments Operations",
  "Digital Channels",
  "Lending Services",
];

const DEPARTMENT_ALIASES = {
  "bank-it support": "Bank-IT Support",
  "bank it support": "Bank-IT Support",
  "it support": "Bank-IT Support",
  "retail banking": "Retail Banking",
  "corporate banking": "Corporate Banking",
  "risk & compliance": "Risk & Compliance",
  "risk and compliance": "Risk & Compliance",
  "payments operations": "Payments Operations",
  "digital channels": "Digital Channels",
  "lending services": "Lending Services",
};

export function normalizeDepartment(value, fallback = null) {
  const normalized = String(value ?? "").trim();

  if (!normalized) {
    return fallback ?? DEPARTMENTS[0];
  }

  if (DEPARTMENTS.includes(normalized)) {
    return normalized;
  }

  const alias = DEPARTMENT_ALIASES[normalized.toLowerCase()];
  if (alias) {
    return alias;
  }

  return fallback ?? normalized;
}
