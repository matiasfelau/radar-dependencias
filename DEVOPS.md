# DevOps Integration Guide

This guide shows how to integrate Dependency Radar into your CI/CD pipelines and infrastructure.

## 1. GitHub Actions Workflow

### Basic Workflow for Python Projects

Create `.github/workflows/dependency-radar.yml`:

```yaml
name: Dependency Radar Scan

on:
  push:
    branches: [main, develop]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Send Python dependencies
        if: hashFiles('requirements*.txt') != ''
        run: |
          curl -X POST "${{ secrets.RADAR_URL }}/api/v1/projects/register" \
            -H "X-API-Key: ${{ secrets.RADAR_API_KEY }}" \
            -F "project_name=${{ github.repository }}" \
            -F "environment=Dev" \
            -F "dependency_file=@requirements.txt"

      - name: Send Node.js dependencies
        if: hashFiles('package.json') != ''
        run: |
          curl -X POST "${{ secrets.RADAR_URL }}/api/v1/projects/register" \
            -H "X-API-Key: ${{ secrets.RADAR_API_KEY }}" \
            -F "project_name=${{ github.repository }}" \
            -F "environment=Dev" \
            -F "dependency_file=@package.json"
```

### Set GitHub Secrets

1. Go to Settings → Secrets and variables → Actions
2. Add:
   - `RADAR_URL`: http://radar.company.com (or http://localhost:8000 for testing)
   - `RADAR_API_KEY`: Generated from your project in Radar dashboard

### Workflow for Production Deployments

```yaml
name: Deploy with Dependency Check

on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'Staging'
        type: choice
        options:
          - Staging
          - Production

jobs:
  register-deps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Register dependencies
        run: |
          curl -X POST "${{ secrets.RADAR_URL }}/api/v1/projects/register" \
            -H "X-API-Key: ${{ secrets.RADAR_API_KEY }}" \
            -F "project_name=${{ github.repository }}" \
            -F "environment=${{ github.event.inputs.environment }}" \
            -F "dependency_file=@requirements.txt"

      - name: Check for critical vulnerabilities
        run: |
          CRITICAL_COUNT=$(curl -s "${{ secrets.RADAR_URL }}/api/v1/alerts/active" \
            | jq '[.items[] | select(.severity=="Critical")] | length')
          if [ "$CRITICAL_COUNT" -gt 0 ]; then
            echo "Found $CRITICAL_COUNT critical vulnerabilities. Blocking deployment."
            exit 1
          fi

  deploy:
    needs: register-deps
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to ${{ github.event.inputs.environment }}
        run: echo "Deploying to ${{ github.event.inputs.environment }}"
```

## 2. GitLab CI Integration

### Basic Pipeline

Create `.gitlab-ci.yml`:

```yaml
variables:
  RADAR_URL: "https://radar.company.com"

stages:
  - scan

dependency-scan:
  stage: scan
  image: curlimages/curl:latest
  script:
    - |
      if [ -f "requirements.txt" ]; then
        curl -X POST "${RADAR_URL}/api/v1/projects/register" \
          -H "X-API-Key: ${RADAR_API_KEY}" \
          -F "project_name=${CI_PROJECT_NAME}" \
          -F "environment=${CI_COMMIT_BRANCH}" \
          -F "dependency_file=@requirements.txt"
      fi
    - |
      if [ -f "package.json" ]; then
        curl -X POST "${RADAR_URL}/api/v1/projects/register" \
          -H "X-API-Key: ${RADAR_API_KEY}" \
          -F "project_name=${CI_PROJECT_NAME}" \
          -F "environment=${CI_COMMIT_BRANCH}" \
          -F "dependency_file=@package.json"
      fi
  only:
    - main
    - develop

vulnerability-check:
  stage: scan
  image: curlimages/curl:latest
  script:
    - |
      CRITICAL=$(curl -s "${RADAR_URL}/api/v1/alerts/active" \
        | jq '[.items[] | select(.severity=="Critical" and .has_exploit==true)] | length')
      if [ "$CRITICAL" -gt 0 ]; then
        echo "⚠️ Found $CRITICAL critical vulnerabilities with exploits"
        exit 1
      fi
  allow_failure: false
  only:
    - main
```

### Set GitLab CI Variables

1. Go to Settings → CI/CD → Variables
2. Add:
   - `RADAR_URL`: https://radar.company.com
   - `RADAR_API_KEY`: (Protected, masked)

## 3. Jenkins Pipeline

```groovy
pipeline {
    agent any
    
    environment {
        RADAR_URL = credentials('radar_url')
        RADAR_API_KEY = credentials('radar_api_key')
    }
    
    stages {
        stage('Register Dependencies') {
            steps {
                script {
                    sh '''
                        if [ -f "requirements.txt" ]; then
                            curl -X POST "${RADAR_URL}/api/v1/projects/register" \
                              -H "X-API-Key: ${RADAR_API_KEY}" \
                              -F "project_name=${JOB_NAME}" \
                              -F "environment=${BRANCH_NAME}" \
                              -F "dependency_file=@requirements.txt"
                        fi
                    '''
                }
            }
        }
        
        stage('Check Vulnerabilities') {
            steps {
                script {
                    sh '''
                        RESPONSE=$(curl -s "${RADAR_URL}/api/v1/alerts/active")
                        CRITICAL=$(echo $RESPONSE | jq '[.items[] | select(.severity=="Critical")] | length')
                        
                        if [ "$CRITICAL" -gt 0 ]; then
                            echo "Found $CRITICAL critical vulnerabilities"
                            exit 1
                        fi
                    '''
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
```

## 4. Container Orchestration (Kubernetes)

### CronJob for Regular Scans

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: dependency-radar-scan
  namespace: security
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: radar-scanner
          containers:
          - name: scanner
            image: curlimages/curl:latest
            env:
            - name: RADAR_URL
              valueFrom:
                configMapKeyRef:
                  name: radar-config
                  key: url
            - name: RADAR_API_KEY
              valueFrom:
                secretKeyRef:
                  name: radar-secrets
                  key: api-key
            - name: PROJECT_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            command:
            - /bin/sh
            - -c
            - |
              curl -X POST "$RADAR_URL/api/v1/projects/register" \
                -H "X-API-Key: $RADAR_API_KEY" \
                -F "project_name=$PROJECT_NAME" \
                -F "environment=Production" \
                -F "dependency_file=@/app/requirements.txt"
            volumeMounts:
            - name: app-deps
              mountPath: /app
          volumes:
          - name: app-deps
            configMap:
              name: app-dependencies
          restartPolicy: OnFailure
```

### ServiceMonitor for Prometheus (Optional)

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: radar-monitor
  namespace: security
spec:
  selector:
    matchLabels:
      app: dependency-radar
  endpoints:
  - port: http
    interval: 30s
    path: /metrics
```

## 5. Webhook Integration

### Slack Notifications

Configure webhook URL in Radar settings:

```
https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Radar will POST:
```json
{
  "event_type": "vulnerability.exploit.detected",
  "cve_id": "CVE-2021-44228",
  "package_name": "log4j",
  "severity": "Critical",
  "has_exploit": true,
  "environment": "Production"
}
```

Create a Slack workflow to parse and format the alert.

### Custom Webhook Handler

```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/webhooks/radar', methods=['POST'])
def handle_radar_alert():
    data = request.json
    
    if data['severity'] == 'Critical' and data['has_exploit']:
        # Send PagerDuty incident
        pagerduty.create_incident(
            title=f"Critical exploit: {data['cve_id']}",
            description=f"{data['package_name']} in {data['environment']}"
        )
    
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(port=5000)
```

## 6. Best Practices

### 1. API Key Management
- Store API keys in secret management systems (Vault, AWS Secrets Manager)
- Rotate keys regularly
- Use different keys per CI/CD platform

### 2. Scan Frequency
- Dev: Every commit or daily
- Staging: Daily or before releases
- Production: Before deployments, plus daily

### 3. Vulnerability Thresholds
```yaml
# Block deployment if:
- Any Critical vulnerability with exploit in Production
- High severity in Staging
- Allow Medium/Low in Dev
```

### 4. Reporting
Pull alerts periodically for dashboards:

```bash
# Get summary
curl "http://radar/api/v1/alerts/active" | jq '.total'

# Filter by environment (requires enhancement)
curl "http://radar/api/v1/projects" | jq '.projects[] | select(.name=="my-app")'
```

### 5. Retention Policy
Configure your database to archive vulnerabilities older than 90 days:

```sql
DELETE FROM vulnerabilities 
WHERE status='Resolved' AND detected_at < NOW() - INTERVAL '90 days';
```

## 7. Troubleshooting

### Connection Refused
- Ensure Radar backend is running: `curl http://localhost:8000/api/v1/health`
- Check firewall rules between CI runner and Radar
- Verify RADAR_URL environment variable

### 401 Unauthorized
- Verify X-API-Key header is set correctly
- Check API key has not been revoked
- Ensure no trailing/leading whitespace in key

### 415 Unsupported Media Type
- Check file extension matches parser (requirements.txt, package.json)
- Ensure Content-Type header is not overriding multipart
