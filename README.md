# Dependency Radar

A comprehensive Software Composition Analysis (SCA) and Threat Intelligence system for monitoring software dependencies across development environments.

## Architecture

```
dependency-radar/
├── backend/          FastAPI + SQLAlchemy + APScheduler
│   ├── src/app/
│   │   ├── api/v1/       REST endpoints (projects, alerts, settings)
│   │   ├── models/       SQLAlchemy ORM (Project, Environment, Dependency, Vulnerability, Setting)
│   │   ├── services/     Business logic (scanning, webhooks, settings)
│   │   ├── parsers/      Dependency file parsers (requirements.txt, package.json)
│   │   └── core/         Config and logging
│   ├── alembic/          Database migrations
│   └── tests/            Unit tests
│
└── frontend/         React + Tailwind + Vite
    ├── src/
    │   ├── components/   Dashboard UI (Inventory, Alerts, Settings)
    │   ├── services/     API client and hooks
    │   └── main.tsx      Entry point
    └── package.json
```

## Stack

**Backend:**
- Python 3.12+
- FastAPI (async API)
- PostgreSQL + SQLAlchemy 2
- APScheduler (background tasks)
- Alembic (migrations)

**Frontend:**
- React 18
- TypeScript
- Tailwind CSS
- Vite (build tool)

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Services available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:8000
# - pgAdmin (optional): http://localhost:5050 --with dev compose

# Stop services
docker-compose down
```

For development with hot-reload:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

See [DOCKER.md](DOCKER.md) for complete Docker documentation.

### Option 2: Manual Local Development

#### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e .[dev]
cp .env.example .env
# Edit .env: DATABASE_URL pointing to PostgreSQL
alembic upgrade head
uvicorn app.main:app --reload
```

Backend available at `http://localhost:8000`

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at `http://localhost:5173`

## API Endpoints

- `POST /api/v1/projects/register` - Ingest dependencies from CI/CD
- `GET /api/v1/projects` - List project inventory
- `GET /api/v1/alerts/active` - Get active vulnerabilities
- `GET /api/v1/settings` - Read scan settings
- `PUT /api/v1/settings` - Update scan settings
- `GET /api/v1/health` - Health check

## Features

### Ingestion (Pipeline-Driven)
- Endpoint: `POST /api/v1/projects/register`
- Accepts multipart upload of dependency files (requirements.txt, package.json)
- Authentication via `X-API-Key` header
- Creates or updates project + environment snapshot

### Vulnerability Scanning
- Background worker runs at configurable interval (default 12 hours)
- Queries OSV.dev for known CVEs
- Reconciles vulnerabilities: marks missing ones as Resolved
- Supports exploit intelligence (simulated with extensible design)

### Notifications
- Webhook outbound for Production vulnerabilities with public exploits
- Configurable retry strategy (exponential backoff)
- Managed via API: `GET/PUT /api/v1/settings`

### Dashboard
- **Inventory**: Projects → Environments → Dependencies
- **Alerts**: Sorted by exploit availability and severity
- **Settings**: Configure scan interval and webhook URL

## Database Schema

- **Projects**: name, api_key, created_at
- **Environments**: project_id, name (Dev/Staging/Production), updated_at
- **Dependencies**: environment_id, package_name, installed_version
- **Vulnerabilities**: cve_id, package_name, affected_version, severity, status, has_exploit, exploit_url
- **Settings**: key-value configuration (scan_interval_seconds in seconds, webhook_url)

## Parsers Supported

- `requirements.txt` (Python)
- `package.json` (Node.js)
- Extensible design for `pom.xml` and others

## MVP Usage Guide

### 1. Dashboard Local

Access at `http://localhost:5173` after running `npm run dev` in frontend/.

**Tabs:**
- **Inventory**: View all projects, their environments (Dev/Staging/Production), and dependency snapshots with timestamps.
- **Alerts**: Real-time list of active vulnerabilities, sorted by exploit availability and severity. Click "Details" to see NVD link.
- **Settings**: Configure scan interval (hours) and webhook URL for outbound notifications.

### 2. DevOps Pipeline Integration

#### GitHub Actions Example

Create `.github/workflows/dependency-scan.yml`:

```yaml
name: Dependency Scan

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Send dependencies to Radar
        run: |
          curl -X POST "http://radar-backend:8000/api/v1/projects/register" \
            -H "X-API-Key: ${{ secrets.RADAR_API_KEY }}" \
            -F "project_name=${{ github.repository }}" \
            -F "environment=Dev" \
            -F "dependency_file=@requirements.txt"
        env:
          RADAR_API_KEY: ${{ secrets.RADAR_API_KEY }}
```

#### GitLab CI Example

Create `.gitlab-ci.yml`:

```yaml
stages:
  - scan

dependency-scan:
  stage: scan
  image: curlimages/curl:latest
  script:
    - |
      curl -X POST "${RADAR_URL}/api/v1/projects/register" \
        -H "X-API-Key: ${RADAR_API_KEY}" \
        -F "project_name=${CI_PROJECT_NAME}" \
        -F "environment=${CI_ENVIRONMENT_NAME}" \
        -F "dependency_file=@package.json"
  variables:
    RADAR_URL: "http://radar-backend:8000"
  only:
    - main
    - develop
```

### 3. API Consumption Examples

#### Register Dependencies

```bash
# Python project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: your-api-key" \
  -F "project_name=payments-service" \
  -F "environment=Production" \
  -F "dependency_file=@requirements.txt"

# Node.js project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: your-api-key" \
  -F "project_name=frontend-app" \
  -F "environment=Staging" \
  -F "dependency_file=@package.json"
```

**Response:**
```json
{
  "project_name": "payments-service",
  "environment": "Production",
  "dependencies_count": 42,
  "updated_at": "2026-05-17T14:30:00Z"
}
```

#### Get Project Inventory

```bash
curl "http://localhost:8000/api/v1/projects"
```

**Response:**
```json
{
  "total_projects": 2,
  "projects": [
    {
      "name": "payments-service",
      "environments": [
        {
          "name": "Production",
          "updated_at": "2026-05-17T14:30:00Z",
          "dependencies": [
            {"package_name": "fastapi", "installed_version": "0.115.0"},
            {"package_name": "sqlalchemy", "installed_version": "2.0.36"}
          ]
        }
      ]
    }
  ]
}
```

#### Get Active Alerts

```bash
curl "http://localhost:8000/api/v1/alerts/active"
```

**Response:**
```json
{
  "total": 1,
  "items": [
    {
      "cve_id": "CVE-2021-44228",
      "package_name": "log4j",
      "affected_version": "2.14.1",
      "severity": "Critical",
      "description": "Apache Log4j2 remote code execution...",
      "has_exploit": true,
      "exploit_url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
      "detected_at": "2026-05-17T12:00:00Z"
    }
  ]
}
```

#### Update Scanner Settings

```bash
curl -X PUT "http://localhost:8000/api/v1/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_interval_seconds": 21600,
    "webhook_url": "https://slack.com/api/webhooks/..."
  }'
```

#### Health Check

```bash
curl "http://localhost:8000/api/v1/health"
# {"status": "ok"}
```

### 4. Webhook Payload Example

When a Production vulnerability with public exploit is detected:

```json
{
  "event_type": "vulnerability.exploit.detected",
  "detected_at": "2026-05-17T14:25:30Z",
  "environment": "Production",
  "cve_id": "CVE-2021-44228",
  "package_name": "log4j",
  "affected_version": "2.14.1",
  "severity": "Critical",
  "has_exploit": true,
  "exploit_url": "https://nvd.nist.gov/vuln/detail/CVE-2021-44228",
  "status": "Active"
}
```

## Future Enhancements

1. **Containerization**: Docker + Compose for reproducible local dev
2. **Multi-format Support**: Add pom.xml, go.mod, Cargo.toml parsers
3. **Real Threat Intelligence**: Integrate NVD, Packet Storm, GitHub Security Advisories
4. **Trend Analytics**: Dashboard showing vulnerability remediation over time
5. **Multi-tenant**: RBAC and project isolation
6. **Compliance**: Generate SBOMs (SPDX format) and compliance reports

## Development

### Run Backend Tests
```bash
cd backend
python -m pytest -q
```

### Lint
```bash
cd backend
python -m ruff check src
```

### Build Frontend
```bash
cd frontend
npm run build
```

## License

MIT
