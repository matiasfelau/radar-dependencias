# Docker Compose Setup Guide

## Quick Start (Production)

```bash
# Clone the repository
git clone https://github.com/your-org/radar-dependencias.git
cd radar-dependencias

# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Database**: localhost:5432 (postgres:5432 from containers)

## Development Mode

Use the development compose file with hot-reload and pgAdmin:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Additional service:
- **pgAdmin**: http://localhost:5050 (admin@radar.local / admin)

## Environment Configuration

### For Production

The default `docker-compose.yml` uses hardcoded credentials. For production, create `.env`:

```bash
cp .env.example .env
```

Edit `.env`:
```
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_strong_password
POSTGRES_DB=dependency_radar
APP_ENV=production
LOG_LEVEL=INFO
```

Then start with:
```bash
docker-compose --env-file .env up -d
```

### Database Credentials

**Default (Development):**
- User: `radar_user`
- Password: `radar_password`
- Database: `dependency_radar`
- Host: `postgres:5432`

Connect from host:
```bash
psql -h localhost -U radar_user -d dependency_radar
# Password: radar_password
```

## Docker Compose Structure

### Production (`docker-compose.yml`)

- **postgres**: Database (no volume by default, set in .env)
- **backend**: FastAPI app, auto-runs migrations on start
- **frontend**: Pre-built React app served by Node
- **pgadmin** (optional, profile: dev): Web-based DB management

### Development (`docker-compose.dev.yml`)

- **postgres**: Database with persistent volume
- **backend**: Python app with live reload (`--reload`)
- **frontend**: Node dev server with hot module replacement
- **pgadmin**: Included by default for debugging

## Common Commands

### Start Services

```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d

# With logs
docker-compose up
```

### Stop Services

```bash
docker-compose down

# Remove volumes (delete all data)
docker-compose down -v
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Restart Service

```bash
docker-compose restart backend
```

### Execute Commands in Container

```bash
# Database access
docker exec -it radar-postgres psql -U radar_user -d dependency_radar

# Backend shell
docker exec -it radar-backend /bin/bash

# Frontend shell
docker exec -it radar-frontend /bin/sh
```

### Rebuild Images

```bash
# Rebuild all
docker-compose build --no-cache

# Rebuild specific
docker-compose build --no-cache backend
```

## Troubleshooting

### Containers won't start

```bash
# Check logs
docker-compose logs

# Check specific service
docker-compose logs backend

# Ensure Docker daemon is running
docker ps
```

### Database connection refused

```bash
# Verify postgres is healthy
docker-compose ps

# Force recreate postgres
docker-compose up -d --force-recreate postgres

# Wait 10 seconds for postgres to be ready
sleep 10
docker-compose up -d backend
```

### Frontend shows blank page

```bash
# Verify backend is reachable
docker exec radar-frontend curl http://backend:8000/api/v1/health

# Check API URL in frontend
docker exec radar-frontend env | grep VITE
```

### Migration fails

```bash
# Check database logs
docker-compose logs postgres

# Manual migration
docker exec -it radar-backend alembic upgrade head
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

## Health Checks

All services have health checks configured:

```bash
# View health status
docker-compose ps

# Manual health check
curl http://localhost:8000/api/v1/health
curl http://localhost:5173
```

## Data Persistence

### Production

Data is stored in Docker volumes managed by Docker:

```bash
# List volumes
docker volume ls | grep radar

# Inspect volume
docker volume inspect radar_dependencias_postgres_data
```

### Development

Data is in `./postgres_data` directory (if using named volume) or inside container.

To backup database:
```bash
docker exec radar-postgres pg_dump -U radar_user dependency_radar > backup.sql
```

To restore:
```bash
docker exec -i radar-postgres psql -U radar_user dependency_radar < backup.sql
```

## Performance Tuning

### For larger deployments

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  postgres:
    environment:
      POSTGRES_INITDB_ARGS: "-c max_connections=200 -c shared_buffers=256MB"
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Test with Docker Compose

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and test
        run: |
          docker-compose build
          docker-compose up -d
          docker-compose exec -T backend python -m pytest
          docker-compose down
```

### GitLab CI

```yaml
test:
  services:
    - docker:dind
  script:
    - docker-compose build
    - docker-compose up -d
    - docker-compose exec -T backend python -m pytest
    - docker-compose down
```

## Networking

All services communicate via the `radar-network`:

- Backend → Postgres: `postgresql://postgres:5432`
- Frontend → Backend: `http://backend:8000`
- pgAdmin → Postgres: `postgres:5432`

From host, use `localhost`:
- Postgres: `localhost:5432`
- Backend: `localhost:8000`
- Frontend: `localhost:5173`

## Security Notes

⚠️ **Development Only**: Default credentials in `docker-compose.yml` are for development.

For production:
1. Generate strong passwords
2. Use `.env` file (not in git)
3. Restrict network exposure
4. Use secrets management (Vault, AWS Secrets Manager)
5. Enable HTTPS (reverse proxy with nginx/traefik)
6. Disable pgAdmin in production

Example production `.env`:
```
POSTGRES_USER=secure_user_xyz
POSTGRES_PASSWORD=$(openssl rand -base64 32)
APP_ENV=production
LOG_LEVEL=WARN
```

## Scaling

For multi-replica setup, use `docker-compose scale`:

```bash
docker-compose up -d --scale backend=3
```

Or with docker service (requires Docker Swarm):

```bash
docker service create --replicas 3 -p 8000:8000 radar-backend
```

For Kubernetes, see `helm/` directory (future enhancement).
