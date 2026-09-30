


┌──────────────┐     HTTPS      ┌────────────────┐     SQL      ┌──────────────┐
│  Frontend    │ ─────────────► │   Backend      │ ───────────► │  PostgreSQL  │
│  React+Nginx │  /api → proxy  │  FastAPI       │              │  (volumen)   │
│  :80/:443    │                │  :8000         │              │  :5432       │
└──────────────┘                └────────────────┘              └──────────────┘
      contenedor 1                  contenedor 2                   contenedor 3


