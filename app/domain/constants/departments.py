KNOWN_DEPARTMENTS = [
    "Bank-IT Support",
    "Retail Banking",
    "Corporate Banking",
    "Risk & Compliance",
    "Payments Operations",
    "Digital Channels",
    "Lending Services",
]

DEFAULT_DEPARTMENT = KNOWN_DEPARTMENTS[0]

_DEPARTMENT_ALIASES = {
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
}

_DEPARTMENT_KEYWORDS = {
    "Payments Operations": [
        "payment",
        "payments",
        "sepa",
        "swift",
        "wire transfer",
        "transfer",
        "iban",
        "direct debit",
        "standing order",
        "settlement",
        "transaction booking",
    ],
    "Retail Banking": [
        "retail banking",
        "branch",
        "atm",
        "savings account",
        "current account",
        "private customer",
        "consumer account",
        "debit card",
    ],
    "Corporate Banking": [
        "corporate banking",
        "business customer",
        "business client",
        "company account",
        "merchant",
        "treasury",
        "cash management",
        "trade finance",
    ],
    "Risk & Compliance": [
        "risk",
        "compliance",
        "aml",
        "kyc",
        "sanction",
        "fraud",
        "regulatory",
        "audit",
        "policy breach",
    ],
    "Digital Channels": [
        "mobile app",
        "mobile banking",
        "web banking",
        "online banking",
        "customer portal",
        "portal",
        "browser",
        "ios",
        "android",
        "push notification",
        "frontend",
        "website",
    ],
    "Lending Services": [
        "loan",
        "lending",
        "mortgage",
        "credit application",
        "underwriting",
        "collateral",
        "repayment",
        "amortization",
    ],
    "Bank-IT Support": [
        "vpn",
        "password",
        "access",
        "login",
        "email",
        "laptop",
        "network",
        "internal system",
        "sso",
        "server",
    ],
}


def normalize_department(value: str | None, fallback: str | None = None) -> str:
    if value:
        normalized = value.strip()
        if normalized in KNOWN_DEPARTMENTS:
            return normalized

        alias = _DEPARTMENT_ALIASES.get(normalized.lower())
        if alias:
            return alias

    if fallback:
        return normalize_department(fallback, DEFAULT_DEPARTMENT)

    return DEFAULT_DEPARTMENT


def canonicalize_department_label(value: str | None, fallback: str | None = None) -> str:
    if value:
        normalized = value.strip()
        if normalized in KNOWN_DEPARTMENTS:
            return normalized

        alias = _DEPARTMENT_ALIASES.get(normalized.lower())
        if alias:
            return alias

        return normalized

    if fallback:
        return canonicalize_department_label(fallback, DEFAULT_DEPARTMENT)

    return DEFAULT_DEPARTMENT


def infer_department_from_text(text: str, fallback: str | None = None) -> str:
    lowered = text.lower()
    scores = dict.fromkeys(KNOWN_DEPARTMENTS, 0)

    for department, keywords in _DEPARTMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in lowered:
                scores[department] += 1

    best_department = max(scores, key=scores.get)
    if scores[best_department] > 0:
        return best_department

    return normalize_department(fallback, DEFAULT_DEPARTMENT)
