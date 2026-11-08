# ARHAM Fintech

Real-time trade data ingestion and monitoring platform built for the ARHAM Fintech technical assessment.

## What is implemented

- React/Vite dashboard with responsive layout, statistics, search, symbol filter, and recent trades.
- FastAPI backend with a deterministic mock BSE feed.
- SQLite persistence through SQLAlchemy.
- Background ingestion jobs with `pending`, `running`, `completed`, and `failed` states.
- Duplicate trade protection using a unique trade ID.
- Server-Sent Events (SSE) for post-commit ingestion notifications.
- SSE event IDs, recent-event replay, browser reconnection, and multiple subscribers.
- API and worker tests.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the system diagram and data flow.

```text
React dashboard
    ├── REST: trades, stats, start/status job
    └── SSE: ingestion.completed / ingestion.failed
             |
         FastAPI
             |
      asyncio background task
             |
       Mock BSE service
             |
        SQLite + SQLAlchemy
```

## Technology stack

| Area | Technology |
|---|---|
| Frontend | React 19, Vite, Axios, Lucide React, Tailwind dependencies |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Persistence | SQLite, SQLAlchemy |
| Live updates | Server-Sent Events |
| Testing | Pytest, pytest-asyncio, HTTPX |

## Requirements

- Node.js and npm
- Python 3.11+
- Git

## Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API is available at <http://localhost:8000>. FastAPI documentation is at
<http://localhost:8000/docs>.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The dashboard is available at <http://localhost:5173>.

## Environment variables

### Backend: `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Application environment label |
| `DATABASE_URL` | `sqlite:///./arham_fintech.db` | SQLAlchemy database URL; relative SQLite paths resolve from the backend working directory |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed browser origin for CORS |

### Frontend: `frontend/.env`

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | FastAPI base URL used by Axios and SSE |

Do not commit `.env` files or credentials.

## API reference

### `GET /health`

Returns `{ "status": "ok" }`.

### `GET /getTrades`

Deterministic mock BSE source.

| Query parameter | Default | Limits |
|---|---:|---|
| `record_count` | `2000` | 1–5000 |
| `delay_seconds` | `0` | 0–900 |
| `seed` | `2026` | 0 or greater |

Example:

```bash
curl "http://localhost:8000/getTrades?record_count=3&seed=7"
```

### `GET /api/trades`

Returns persisted trades ordered newest first.

| Query parameter | Default | Limits |
|---|---:|---|
| `page` | `1` | 1 or greater |
| `page_size` | `50` | 1–200 |
| `symbol` | — | Optional symbol |
| `search` | — | Searches trade ID, client, and symbol |

### `POST /api/trades/pull`

Creates an ingestion job and returns `202 Accepted` immediately.

Supports the same `record_count`, `delay_seconds`, and `seed` query parameters
as the mock feed.

```bash
curl -X POST "http://localhost:8000/api/trades/pull?record_count=10&seed=7"
```

### `GET /api/trades/pull/{job_id}`

Returns job status, timestamps, saved record count, and any error message.

### `GET /api/trades/stats`

Returns total trades, unique clients, unique symbols, and total trade value.

### `GET /api/trades/stream`

SSE stream used by the dashboard. Events:

- `ingestion.completed`
- `ingestion.failed`

Each event includes an ID. The server replays recent events after a browser
reconnect using `Last-Event-ID`.

## Background ingestion and SSE

`POST /api/trades/pull` creates a database job, schedules an in-process
`asyncio` task, and returns without waiting for the exchange delay. The worker:

1. Marks the job `running`.
2. Fetches mock BSE records.
3. Saves new trades in SQLite.
4. Commits the transaction.
5. Publishes an SSE event only after the commit.
6. Marks failures with an error message and publishes `ingestion.failed`.

The React dashboard opens one `EventSource`. On a completion or failure event it
fetches authoritative job status, trades, and statistics. It does not poll.

## Testing

Backend tests:

```bash
cd backend
.venv/bin/pytest -q
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

Phase 9 validation result: **16 backend tests passed**, frontend build passed,
and frontend lint passed with one existing non-blocking React effect advisory.
The live workflow also verified immediate job acceptance, background completion,
SSE delivery to two clients, and persisted refreshed data.

## Project structure

```text
backend/
  app/
    api/          REST and SSE routes
    core/         Settings
    database/     SQLAlchemy engine and sessions
    models/       Trade and ingestion job models
    schemas/      Pydantic response models
    services/     Mock feed, persistence, and SSE broker
    workers/      Background ingestion task
  tests/
frontend/
  src/
    components/   Dashboard UI components
    hooks/        Dashboard data and SSE integration
    services/     Axios API client
docs/
  architecture.md
```

## Video demonstration script

Target length: 2–3 minutes.

1. Show the repository and briefly identify `frontend/`, `backend/`, and SQLite.
2. Start Uvicorn and Vite; open the dashboard.
3. Point out initial statistics and persisted recent trades.
4. Click **Start data pull** and show the job status changing from pending/running
   to completed while the dashboard remains usable.
5. Highlight the live connection indicator and show new records/statistics
   appearing without a page refresh.
6. Open a second browser tab to demonstrate multiple connected clients.
7. Refresh the page and show that persisted trades remain available.
8. End by showing `pytest`, `npm run lint`, and `npm run build` results.

## GitHub submission checklist

- [ ] Push the complete repository, including `README.md` and `docs/architecture.md`.
- [ ] Confirm `.env`, databases, virtual environments, `node_modules`, and build output are ignored.
- [ ] Confirm `backend/.env.example` and `frontend/.env.example` are present.
- [ ] Run backend tests and frontend lint/build from a clean checkout.
- [ ] Verify both startup commands in the README.
- [ ] Verify the README API examples use the current routes.
- [ ] Add the assessment video link after recording.
- [ ] Confirm no secrets or local credentials are committed.

## Known limitations

- The worker is in-process; stopping the API stops active ingestion jobs.
- SQLite and the in-memory SSE broker are intended for this assessment, not
  multi-instance production deployment.
- The frontend currently has no authentication or authorization layer.
