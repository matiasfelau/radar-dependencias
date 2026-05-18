# Docker Compose Files Reference

This project includes two Docker Compose configurations for different use cases.

## Overview

| Feature | `docker-compose.yml` | `docker-compose.dev.yml` |
|---------|---------------------|-------------------------|
| **Purpose** | Production/testing | Development (hot-reload) |
| **Backend** | Pre-built image | Live source reload |
| **Frontend** | Pre-built static app | Dev server with HMR |
| **pgAdmin** | Optional (profile) | Always included |
| **Auto-migrate** | Yes (on startup) | Manual run |
| **Node modules** | In image | Volume mount |
| **Best for** | CI/CD, demo | Active development |
| **Startup time** | ~30s | ~15s (after first build) |

## `docker-compose.yml` (Production)

### When to Use
- Testing deployment setup
- CI/CD pipelines
- Demo environments
- Production-like validation

### Services

```yaml
postgres:
  - Image: postgres:16-alpine
  - Data: Persistent volume (postgres_data)
  - Network: radar-network

backend:
  - Build: ./backend (Dockerfile)
  - Auto-runs: alembic upgrade + uvicorn
  - Ports: 8000:8000
  - Depends on: postgres (health check)

frontend:
  - Build: ./frontend (multi-stage: build → nginx)
  - Serves: Pre-built React app
  - Ports: 5173:5173

pgadmin (optional):
  - Profile: dev
  - Ports: 5050:80
```

### Database Initialization
- Runs automatically on first start
- Migrations: `alembic upgrade head` (in container entrypoint)
- Seed data: Applied during initial migration

### Usage

```bash
# Start (production mode)
docker-compose up -d

# View status
docker-compose ps

# Check backend logs
docker-compose logs backend

# Run one-off command
docker-compose exec backend alembic downgrade -1

# Stop
docker-compose down

# Stop and remove data
docker-compose down -v
```

### Customization with .env

Create `.env` file:
```
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mysecurepass
POSTGRES_DB=dependency_radar
APP_ENV=production
LOG_LEVEL=WARN
```

Use it:
```bash
docker-compose --env-file .env up -d
```

## `docker-compose.dev.yml` (Development)

### When to Use
- Active feature development
- Debugging and testing
- Rapid iteration (hot-reload)
- Database exploration (pgAdmin)

### Services

```yaml
postgres:
  - Image: postgres:16-alpine
  - Data: Persistent volume (postgres_data)
  - Network: radar-network-dev

backend:
  - No build: Uses python:3.12-slim
  - Source: Mounted volume (./backend/src)
  - Command: uvicorn with --reload
  - Ports: 8000:8000
  - HMR: Yes (watches src/)
  - Depends on: postgres

frontend:
  - No build: Uses node:18-alpine
  - Command: npm run dev (Vite dev server)
  - Ports: 5173:5173
  - HMR: Yes (hot module replacement)
  - Volumes: ./frontend (with node_modules exclusion)

pgadmin:
  - Image: dpage/pgadmin4:latest
  - Always included
  - Ports: 5050:80
  - Web UI for database management
```

### Key Features

**Live Source Reload:**
- Backend changes to `src/` auto-reload app
- Frontend changes to `src/` hot-reload in browser
- No rebuild needed

**Database:**
- Auto-applies migrations
- pgAdmin available for schema exploration
- Local volume persistence

### Usage

```bash
# Start (development mode)
docker-compose -f docker-compose.dev.yml up -d

# Watch logs (useful during development)
docker-compose -f docker-compose.dev.yml logs -f

# Backend bash shell
docker-compose -f docker-compose.dev.yml exec backend bash

# Run tests with rebuild
docker-compose -f docker-compose.dev.yml exec backend python -m pytest

# Database access
docker-compose -f docker-compose.dev.yml exec postgres psql -U radar_user -d dependency_radar

# pgAdmin
# Open browser: http://localhost:5050
# Login: admin@radar.local / admin
# Create server connection:
#   - Hostname: postgres
#   - Port: 5432
#   - Username: radar_user
#   - Password: radar_password

# Stop
docker-compose -f docker-compose.dev.yml down
```

## Switching Between Modes

### From Production to Development

```bash
# Stop production
docker-compose down

# Start development
docker-compose -f docker-compose.dev.yml up -d
```

### From Development to Production

```bash
# Stop development
docker-compose -f docker-compose.dev.yml down

# Build production images
docker-compose build

# Start production
docker-compose up -d
```

**Note:** Volumes are shared between modes, so database state persists.

## Volume Management

### Shared Volumes

Both configurations can use the same named volume:

```bash
# List all radar volumes
docker volume ls | grep radar

# Inspect postgres data
docker volume inspect radar_dependencias_postgres_data

# Backup database
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  postgres:16-alpine tar czf /backup/db_backup.tar.gz -C /data .

# Restore database
docker run --rm -v postgres_data:/data -v $(pwd):/backup \
  postgres:16-alpine tar xzf /backup/db_backup.tar.gz -C /data
```

### Development Volumes

In `docker-compose.dev.yml`:

```yaml
volumes:
  - ./backend/src:/app/src          # Backend source (live reload)
  - ./backend/alembic:/app/alembic  # Migrations
  - ./frontend:/app                 # Frontend source
  - /app/node_modules               # Exclude node_modules (named volume)
```

These are **dev-only** volumes for hot-reload.

## Service-to-Service Communication

### Within Compose Network

Services can communicate using service names:

```
backend → postgres: postgresql://postgres:5432/...
frontend → backend: http://backend:8000/...
pgadmin → postgres: postgres:5432
```

### From Host Machine

Use `localhost`:

```
postgres: localhost:5432
backend:  localhost:8000
frontend: localhost:5173
pgadmin:  localhost:5050
```

### Example: Backend to Database

In backend code (running in container):

```python
# Inside container, use service name
database_url = "postgresql+psycopg://radar_user:password@postgres:5432/dependency_radar"
```

In shell from host:

```bash
# From host machine, use localhost
psql -h localhost -U radar_user -d dependency_radar
```

## Networking

### Compose Networks

```bash
# List compose networks
docker network ls | grep radar

# Inspect network
docker network inspect radar_dependencias_radar-network

# Test connectivity
docker-compose exec backend curl http://postgres:5432
```

## Troubleshooting

### Services don't start

```bash
# Check all services
docker-compose ps

# Check specific service logs
docker-compose logs postgres
docker-compose logs backend
docker-compose logs frontend

# Rebuild images
docker-compose build --no-cache
```

### Backend can't connect to database

```bash
# Verify postgres is healthy
docker-compose exec postgres pg_isready

# Check connection from backend
docker-compose exec backend python -c \
  "from sqlalchemy import create_engine; \
   engine = create_engine('postgresql+psycopg://radar_user:radar_password@postgres/dependency_radar'); \
   print(engine.execute('SELECT 1'))"
```

### Frontend can't reach backend

```bash
# From frontend container
docker-compose exec frontend curl http://backend:8000/api/v1/health

# From host
curl http://localhost:8000/api/v1/health
```

### Port already in use

Change ports in docker-compose.yml:

```yaml
services:
  backend:
    ports:
      - "8001:8000"  # Changed from 8000
  frontend:
    ports:
      - "5174:5173"  # Changed from 5173
```

### Hot-reload not working

In dev mode:

```bash
# Restart with verbose logging
docker-compose -f docker-compose.dev.yml restart -v

# Check file watching
docker-compose -f docker-compose.dev.yml exec backend \
  ps aux | grep uvicorn
```

Ensure source files are in correct locations:
- Backend: `./backend/src/**`
- Frontend: `./frontend/src/**`

## Performance Tips

### Reduce Image Size

Prod backend uses `python:3.12-slim` (base ~120MB):

```bash
# Check image sizes
docker images | grep radar

# Cleanup unused images
docker image prune
```

### Speed Up Development

Use tmpfs for faster I/O:

```yaml
services:
  backend:
    tmpfs:
      - /tmp
      - /var/tmp
```

### Database Performance

Add to postgres in docker-compose.dev.yml:

```yaml
environment:
  POSTGRES_INITDB_ARGS: "-c max_connections=200 -c shared_buffers=256MB"
```

## Integration Examples

### GitHub Actions CI/CD

```yaml
- name: Start Docker Compose
  run: |
    docker-compose -f docker-compose.yml up -d
    docker-compose exec -T postgres pg_isready -U radar_user
    
- name: Run Tests
  run: docker-compose exec -T backend python -m pytest

- name: Cleanup
  run: docker-compose down -v
```

### Pre-commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Ensure containers are running
docker-compose ps | grep -q backend || docker-compose up -d

# Run linting
docker-compose exec -T backend ruff check src
docker-compose exec -T backend mypy src

exit $?
```

## Makefile Commands

Quick shortcuts for common operations:

```bash
make up-prod          # Start production
make up-dev           # Start development
make down             # Stop services
make logs-backend     # View backend logs
make shell-backend    # Open backend shell
make test             # Run tests
make clean            # Remove all containers/volumes
```

See [Makefile](Makefile) for complete list.
