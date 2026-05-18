# Getting Started with Dependency Radar

This guide walks you through setting up and using Dependency Radar locally.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD Pipelines                              │
│              (GitHub Actions, GitLab, Jenkins)                   │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                    POST /projects/register
                    (requirements.txt, package.json)
                                │
                ┌───────────────▼────────────────┐
                │   Dependency Radar Backend     │
                │   (FastAPI + PostgreSQL)       │
                ├───────────────────────────────┤
                │ • REST APIs                    │
                │ • APScheduler (OSV scans)      │
                │ • Webhook notifications        │
                └───────────────┬────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
      Webhook          REST API          Database
      (Slack/email)     (JSON)            (PostgreSQL)
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
                ┌───────────────▼────────────────┐
                │  Dependency Radar Dashboard    │
                │   (React + Tailwind)           │
                └───────────────────────────────┘
```

## Quick Start (Docker Compose) - Recommended ⭐

The fastest way to get started is using Docker Compose.

### Prerequisites

- **Docker** - [Install Docker Desktop](https://www.docker.com/products/docker-desktop)
- **docker-compose** - Usually included with Docker Desktop

### Start All Services

```bash
# Clone the repository
git clone https://github.com/your-org/radar-dependencias.git
cd radar-dependencias

# Start services (production mode)
docker-compose up -d

# Or start with development hot-reload
docker-compose -f docker-compose.dev.yml up -d
```

### Access Services

```
Frontend:     http://localhost:5173
Backend API:  http://localhost:8000
API Docs:     http://localhost:8000/docs
pgAdmin*:     http://localhost:5050
```

*pgAdmin included in development mode for database exploration

### First Test

```bash
# 1. Open http://localhost:5173 in your browser
# 2. Go to "Settings" tab
# 3. Set scan interval to 1 hour and save
# 4. Register a test project using the curl command below
# 5. View results in "Inventory" and "Alerts" tabs

# Register a test project
curl -X POST 'http://localhost:8000/api/v1/projects/register' \
  -H 'X-API-Key: default-api-key' \
  -F 'project_name=test-app' \
  -F 'environment=Dev' \
  -F 'dependency_file=@path/to/requirements.txt'
```

### Stop Services

```bash
docker-compose down           # Stop (keep data)
docker-compose down -v        # Stop and delete data
```

### Quick Commands

```bash
# View logs
docker-compose logs -f backend

# Run tests
docker-compose exec backend python -m pytest

# Access database
docker-compose exec postgres psql -U radar_user -d dependency_radar

# Open backend shell
docker-compose exec backend bash
```

For more Docker options, see [DOCKER.md](DOCKER.md) and [COMPOSE.md](COMPOSE.md).

---

## Manual Setup (Local Development)

If you prefer not to use Docker, follow these steps.

### Prerequisites

- **Python 3.12+** - For backend
- **PostgreSQL 14+** - Database
- **Node.js 18+** - For frontend
- **Git** - Version control

## 1. Backend Setup

### Step 1: Install Backend Dependencies

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -e .[dev]
```

### Step 2: Configure Database

```bash
cp .env.example .env
```

Edit `.env`:
```
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/dependency_radar
LOG_LEVEL=INFO
```

If PostgreSQL is not installed, you can use Docker:
```bash
docker run --name postgres-radar -e POSTGRES_PASSWORD=postgres -d -p 5432:5432 postgres:16
```

### Step 3: Run Migrations

```bash
alembic upgrade head
```

This creates all tables and seeds `scan_interval_seconds=43200` (12 hours).

### Step 4: Start Backend

```bash
uvicorn app.main:app --reload
```

Backend is ready at `http://localhost:8000`

Test it:
```bash
curl http://localhost:8000/api/v1/health
# {"status": "ok"}
```

## 2. Frontend Setup

### Step 1: Install Frontend Dependencies

```bash
cd frontend
npm install
```

### Step 2: Start Development Server

```bash
npm run dev
```

Frontend is ready at `http://localhost:5173`

## 3. Using the Dashboard

### Register a Project

Before seeing anything in the dashboard, you need to register a project with dependencies.

```bash
cd /path/to/your/python/project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: default-api-key" \
  -F "project_name=my-python-app" \
  -F "environment=Dev" \
  -F "dependency_file=@requirements.txt"
```

### View Inventory

Navigate to `http://localhost:5173` → **Inventory** tab

You'll see:
- Project: my-python-app
- Environment: Dev
- Dependencies list with versions

### View Alerts

Click **Alerts** tab

The backend runs a vulnerability scan every 12 hours (configurable). For testing:
```bash
# Manually trigger a scan by stopping and restarting the backend
# Or wait 12 hours
```

Once the scan runs, you'll see any detected CVEs.

### Configure Settings

Click **Settings** tab to:
- Change scan interval (default: 12 hours)
- Add webhook URL for notifications (e.g., Slack)

```bash
# Example: Update to 6-hour scan interval
curl -X PUT "http://localhost:8000/api/v1/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_interval_seconds": 21600,
    "webhook_url": "https://slack.com/api/webhooks/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"
  }'
```

## 4. Testing the API

### Register Multiple Projects

```bash
# Python project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: default-api-key" \
  -F "project_name=payments-api" \
  -F "environment=Production" \
  -F "dependency_file=@requirements.txt"

# Node.js project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: default-api-key" \
  -F "project_name=web-app" \
  -F "environment=Staging" \
  -F "dependency_file=@package.json"
```

### Get Inventory

```bash
curl "http://localhost:8000/api/v1/projects" | jq
```

Response:
```json
{
  "total_projects": 2,
  "projects": [
    {
      "name": "payments-api",
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

### Get Alerts

```bash
curl "http://localhost:8000/api/v1/alerts/active" | jq
```

### Update Settings

```bash
curl -X PUT "http://localhost:8000/api/v1/settings" \
  -H "Content-Type: application/json" \
  -d '{
    "scan_interval_seconds": 21600,
    "webhook_url": ""
  }' | jq
```

## 5. Integrating with Your CI/CD

### GitHub Actions Example

Create `.github/workflows/dependency-radar.yml`:

```yaml
name: Dependency Radar

on:
  push:
    branches: [main]

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          curl -X POST "http://localhost:8000/api/v1/projects/register" \
            -H "X-API-Key: default-api-key" \
            -F "project_name=${{ github.repository }}" \
            -F "environment=Dev" \
            -F "dependency_file=@requirements.txt"
```

## 6. Stopping Everything

```bash
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)
# Optional: Stop PostgreSQL
docker stop postgres-radar
```

## 7. Next Steps

- Read [DEVOPS.md](DEVOPS.md) for detailed CI/CD integration examples
- Explore backend [README.md](backend/README.md) for API documentation
- Explore frontend [README.md](frontend/README.md) for component details
- Check database schema in [backend/alembic/versions/](backend/alembic/versions/)

## Troubleshooting

### Backend won't start
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT 1"

# Check logs
tail -f backend_logs.txt
```

### Frontend can't reach backend
```bash
# Verify backend is running
curl http://localhost:8000/api/v1/health

# Check vite proxy in frontend/vite.config.ts
```

### No dependencies showing in dashboard
```bash
# Make sure you've registered at least one project
curl -X POST "http://localhost:8000/api/v1/projects/register" \
  -H "X-API-Key: default-api-key" \
  -F "project_name=test" \
  -F "environment=Dev" \
  -F "dependency_file=@requirements.txt"
```

### Alerts not showing
```bash
# Wait for scan (every 12 hours by default)
# Or manually trigger: restart backend to run scan on startup

# Check settings
curl "http://localhost:8000/api/v1/settings" | jq
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/projects/register | Register dependency snapshot |
| GET | /api/v1/projects | List project inventory |
| GET | /api/v1/alerts/active | Get active vulnerabilities |
| GET | /api/v1/settings | Read scanner config |
| PUT | /api/v1/settings | Update scanner config |
| GET | /api/v1/health | Health check |

For detailed examples, see [README.md](README.md) "API Consumption Examples" section.
