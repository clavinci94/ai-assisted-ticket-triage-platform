# Frontend Architecture

The frontend follows the repository's layered organization and separates UI, orchestration, domain rules, and technical adapters.

## Source Structure

```text
src
├── application
│   ├── notifications
│   └── tickets
├── domain
│   └── constants
├── infrastructure
│   ├── http
│   └── storage
├── interfaces
│   ├── components
│   └── pages
├── App.css
├── App.jsx
└── main.jsx
```

## Layer Responsibilities

- `interfaces`: React pages and visual components
- `application`: client-side workflows and UI orchestration
- `domain`: business-facing constants and normalization helpers
- `infrastructure`: HTTP access, local storage, and external technical adapters

`App.jsx` remains the composition root for routing and shell layout.
