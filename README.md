# ARHAM Fintech – Real-Time Trade Data Ingestion & Monitoring Platform

A real-time trade data ingestion and monitoring platform developed as part of the ARHAM Fintech Software Engineer technical assessment.

The application simulates fetching trade records from a BSE-like API, processes long-running ingestion jobs in the background, persists trade data, and updates the dashboard automatically using Server-Sent Events (SSE).

## Features

- **Real-Time Dashboard:** Displays trade statistics, recent trades, search, and symbol filtering.
- **Mock BSE API:** Generates deterministic trade data with configurable record counts, delays, and seeds.
- **Asynchronous Ingestion:** Starts ingestion jobs without keeping the HTTP request open.
- **Job Tracking:** Supports `pending`, `running`, `completed`, and `failed` states.
- **Persistent Storage:** Uses SQLite and SQLAlchemy to store trades and ingestion jobs.
- **Duplicate Prevention:** Uses unique trade IDs to prevent duplicate records.
- **Server-Sent Events:** Notifies connected dashboards when ingestion completes or fails.
- **SSE Reconnection:** Supports event IDs, recent-event replay, browser reconnection, and multiple subscribers.
- **Testing:** Includes backend API and worker tests.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the architecture diagram and design explanation.

### System Overview

```text
             React Dashboard
                    |
          +---------+---------+
          |                   |
      REST API              SSE
          |                   |
          +---------+---------+
                    |
                FastAPI
                    |
          Background Worker
                    |
             Mock BSE API
                    |
          SQLite + SQLAlchemy
                    |
              SSE Broker
```

### Design Decisions

| Component | Responsibility |
|---|---|
| React | Dashboard and user interface |
| FastAPI | REST endpoints and job management |
| Background Worker | Processes long-running ingestion jobs |
| Mock BSE API | Simulates the external trade data source |
| SQLite | Persistent storage for trades and jobs |
| SSE | Sends ingestion completion and failure notifications |

The background worker and SSE broker run in-process for this assessment. A production deployment with multiple backend instances would require durable job processing and shared event infrastructure.

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | React 19, Vite, Axios, Tailwind CSS, Lucide React |
| Backend | Python, FastAPI, Uvicorn, Pydantic |
| Database | SQLite, SQLAlchemy |
| Background Processing | Python asyncio |
| Live Updates | Server-Sent Events (SSE) |
| Testing | Pytest, pytest-asyncio, HTTPX |

## Requirements

- Python 3.11 or later
- Node.js and npm
- Git

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/jeswin08/Arham-Fintech.git
cd Arham-Fintech
```

### 2. Backend Setup

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env

uvicorn app.main:app --reload
```

Backend API:

- Base URL: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### 3. Frontend Setup

Open a second terminal from the project root:

```bash
cd frontend

npm install

cp .env.example .env

npm run dev
```

Frontend dashboard:

http://localhost:5173

## Environment Variables

### Backend – `backend/.env`

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Application environment |
| `DATABASE_URL` | `sqlite:///./arham_fintech.db` | SQLAlchemy database connection |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | Allowed frontend origin for CORS |

### Frontend – `frontend/.env`

| Variable | Default | Description |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend API base URL |

Do not commit `.env` files or credentials.

## API Reference

### 1. Health Check

`GET /health`

Checks whether the backend is running.

### 2. Mock BSE API

`GET /getTrades`

Generates deterministic mock trade records.

| Parameter | Default | Limits |
|---|---:|---|
| `record_count` | `2000` | 1–5000 |
| `delay_seconds` | `0` | 0–900 |
| `seed` | `2026` | 0 or greater |

Example:

```bash
curl "http://localhost:8000/getTrades?record_count=3&seed=7"
```

### 3. Get Trades

`GET /api/trades`

Returns persisted trade records.

| Parameter | Default | Description |
|---|---:|---|
| `page` | `1` | Page number |
| `page_size` | `50` | Records per page (maximum 200) |
| `symbol` | — | Optional symbol filter |
| `search` | — | Searches trade ID, client, and symbol |

### 4. Start Ingestion

`POST /api/trades/pull`

Starts a background ingestion job and immediately returns `202 Accepted` with a job ID.

Example:

```bash
curl -X POST "http://localhost:8000/api/trades/pull?record_count=10&seed=7"
```

The client does not need to wait for the complete ingestion process.

### 5. Get Job Status

`GET /api/trades/pull/{job_id}`

Returns the ingestion job status, timestamps, processed record count, inserted record count, and error details when applicable.

### 6. Dashboard Statistics

`GET /api/trades/stats`

Returns:

- Total trades
- Unique clients
- Unique symbols
- Total trade value

### 7. SSE Event Stream

`GET /api/trades/stream`

Provides live ingestion notifications.

Supported events:

- `ingestion.completed`
- `ingestion.failed`

Events include unique IDs. The server supports replaying recent events using the `Last-Event-ID` header when a client reconnects.

## Ingestion Workflow

The ingestion process follows these steps:

1. The frontend sends a `POST /api/trades/pull` request.
2. The backend creates an ingestion job with a unique job ID.
3. The API immediately returns the job ID and initial status.
4. A background worker processes the ingestion independently.
5. The worker fetches records from the Mock BSE API.
6. New trade records are saved to SQLite, while duplicate trade IDs are skipped.
7. The database transaction is committed.
8. The backend publishes an SSE completion or failure event.
9. The frontend receives the event and fetches updated trades, job status, and dashboard statistics.

The dashboard uses a single EventSource connection for live updates. It does not rely on polling or manual page refreshes.

## Testing

### Backend Tests

```bash
cd backend
.venv/bin/pytest -q
```

### Frontend Checks

```bash
cd frontend
npm run lint
npm run build
```

### Validation

The Phase 9 validation recorded:

- 16 backend tests passed.
- Frontend production build passed.
- Frontend lint passed with one existing non-blocking React effect advisory.
- Live workflow verified immediate job acceptance, background completion, SSE delivery to two clients, and refreshed persisted data.

## Project Structure

```text
Arham-Fintech/
│
├── backend/
│   ├── app/
│   │   ├── api/          # REST and SSE routes
│   │   ├── core/         # Application settings
│   │   ├── database/     # Database configuration
│   │   ├── models/       # Trade and job models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Mock feed, persistence, SSE broker
│   │   └── workers/      # Background ingestion worker
│   └── tests/
│
├── frontend/
│   └── src/
│       ├── components/   # Dashboard components
│       ├── hooks/        # Dashboard and SSE hooks
│       └── services/     # API client
│
├── docs/
│   └── architecture.md
│
└── README.md
```

## Assessment Scope

This project uses a deterministic Mock BSE API rather than a live exchange connection.

The background worker and SSE broker are implemented in-process to keep the assessment solution simple. Production deployment would require durable background job execution and shared event infrastructure for reliability across multiple backend instances.

## Author

**Jeswin Chacko**
