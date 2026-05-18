# Dependency Radar Backend

FastAPI backend for Software Composition Analysis and vulnerability management.

## Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- pip

### Setup

```bash
# Clone and navigate
git clone https://github.com/your-org/radar-dependencias.git
cd radar-dependencias/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On macOS/Linux

# Install dependencies
python -m pip install -e .[dev]

# Configure environment
cp .env.example .env
# Edit .env: set DATABASE_URL to your PostgreSQL instance
# Example: DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/dependency_radar

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

## Environment Variables

- `APP_NAME`: Application title (default: "Dependency Radar")
- `APP_ENV`: Environment name (default: "development")
- `DATABASE_URL`: PostgreSQL connection string (required)
- `LOG_LEVEL`: Logging level (default: "INFO")

## Project Layout

- `src/app/main.py`: FastAPI entrypoint with lifespan management
- `src/app/core`: Configuration, logging setup
- `src/app/db`: SQLAlchemy engine, session management, Base ORM
- `src/app/models`: ORM entities (Project, Environment, Dependency, Vulnerability, Setting)
- `src/app/parsers`: Dependency file parsers (requirements.txt, package.json)
- `src/app/services`: Business logic (scanning, webhooks, inventory, settings)
- `src/app/api/v1`: REST endpoints (projects, alerts, settings)
- `alembic`: Database migrations
- `tests`: Unit tests

## Ingestion endpoint

`POST /api/v1/projects/register`

Expected multipart fields:

- `project_name`: string
- `environment`: `Dev` | `Staging` | `Production`
- `dependency_file`: upload file (`requirements.txt` or `package.json`)

Required header:

- `X-API-Key`: project API key used by CI/CD pipeline

Example using `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/projects/register" \
   -H "X-API-Key: your-project-key" \
   -F "project_name=payments-service" \
   -F "environment=Production" \
   -F "dependency_file=@requirements.txt"
```

## Alerts endpoints

`GET /api/v1/alerts/active`

Returns all active vulnerabilities sorted by exploit availability and detection time.

`POST /api/v1/alerts/debug/scan` (development only)

Manually trigger the vulnerability scanner. Useful for testing without waiting for the background scheduler.

Response:
```json
{
  "activated": 5,
  "resolved": 0,
  "scanned_pairs": 10
}
```

## How Vulnerability Scanning Works

1. **Dependency Registration**: When you `POST /api/v1/projects/register`, dependencies are stored with package name and version.
2. **Background Scanner**: Every `scan_interval_seconds`, APScheduler runs `scan_vulnerabilities()`.
3. **OSV Query**: For each unique package/version pair, queries [OSV.dev](https://osv.dev) API.
4. **Exploit Detection**: For each CVE found, checks if a public exploit exists and if the dependency is in Production.
5. **Webhook Alert**: If exploit found in Production, sends webhook notification.
6. **Status Tracking**: Marks vulnerabilities as ACTIVE or RESOLVED based on current dependencies.

### Supported Vulnerability Sources

- **OSV.dev**: Open Source Vulnerabilities (Python, npm, Rust, etc.)
- **NVD**: National Vulnerability Database (auto-linked for any CVE)
- **Known Exploits**: Hardcoded database of public exploits

## Settings endpoints

- `GET /api/v1/settings`: reads current scanner settings.
- `PUT /api/v1/settings`: updates `scan_interval_seconds` and `webhook_url`.

Request body example:

```json
{
   "scan_interval_seconds": 21600,
   "webhook_url": "https://example.com/webhooks/security"
}
```

(21600 seconds = 6 hours)

## Background scanner

- Uses APScheduler in-process background worker.
- Reads `scan_interval_seconds` dynamically from Settings table.
- Queries OSV.dev using unique package/version pairs.
- Marks missing vulnerabilities as `Resolved`.
- Sends outbound webhook when a newly detected vulnerability has a public exploit and affects Production.
