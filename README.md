# IT Helpdesk Diagnostic API — Backend

A FastAPI backend for an IT support diagnostic portal. This API runs basic network diagnostic checks, returns structured diagnostic results, and generates mock support tickets for troubleshooting workflows.

## Project Purpose

This backend was built as part of a full-stack portfolio project to demonstrate practical IT support automation, API development, backend error handling, and deployment-safe diagnostic behavior.

The API connects to a React/Vite frontend deployed on Vercel.

Frontend: https://it-support-diagnostic-portal.vercel.app

## Tech Stack

- Python
- FastAPI
- Pydantic
- Uvicorn
- Socket programming
- ThreadPoolExecutor
- Render deployment

## Features

- Accepts a domain or IP address for diagnostic testing
- Performs DNS resolution
- Runs ping checks when the system command is available
- Falls back to TCP reachability checks when `ping` is unavailable
- Runs traceroute when the system command is available
- Returns clean cloud-safe traceroute fallback messages when unavailable
- Scans common ports: 21, 22, 80, 443, and 3389
- Generates mock support ticket IDs
- Includes a health check endpoint for deployment monitoring

## API Endpoints

### Root

```http
GET /
```

Returns basic API status.

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok"
}
```

### Run Diagnostics

```http
POST /api/diagnostics
```

Example request:

```json
{
  "target": "google.com"
}
```

Example response structure:

```json
{
  "timestamp": "2026-05-29T00:00:00",
  "target": "google.com",
  "results": {
    "ping": "Reachability output here",
    "traceroute": "Route diagnostic output here",
    "ports": {
      "21": "Closed",
      "22": "Closed",
      "80": "Open",
      "443": "Open",
      "3389": "Closed"
    }
  }
}
```

### Generate Support Ticket

```http
POST /api/ticket
```

Example request:

```json
{
  "user_id": "Demo Agent",
  "target": "google.com",
  "ping_data": "Reachability output here",
  "traceroute_data": "Route diagnostic output here"
}
```

Example response:

```json
{
  "status": "success",
  "message": "Ticket TKT-20260529123456 successfully created.",
  "ticket_id": "TKT-20260529123456",
  "data_logged": {
    "user": "Demo Agent",
    "issue_target": "google.com"
  }
}
```

## Cloud Deployment Behavior

Some hosted server environments do not provide system-level commands like `ping` or `traceroute`.

Instead of returning raw server errors, this backend handles those cases gracefully:

- If `ping` is unavailable, the API runs a TCP reachability check.
- If `traceroute` is unavailable, the API returns a clean explanation.
- Port scanning and DNS resolution still work.

This makes the deployed app safer and more reliable for portfolio demonstration.

## Run Locally

Create and activate a virtual environment:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn app.main:app --reload
```

The API will run at:

```text
http://127.0.0.1:8000
```

## API Docs

Local API docs:

```text
http://127.0.0.1:8000/docs
```

Production API docs:

```text
https://it-support-api-g0b4.onrender.com/docs
```

## Frontend Repository

Frontend repo: `AC0731/it-helpdesk-frontend`

Live frontend:

```text
https://it-support-diagnostic-portal.vercel.app
```

## Testing Completed

The backend was tested with:

```bash
python -m py_compile app/services/network_tools.py
```

The API was also tested locally using FastAPI Swagger docs with:

```http
POST /api/diagnostics
```

using:

```json
{
  "target": "google.com"
}
```

## Author

Akanksha Chavda  
GitHub: AC0731