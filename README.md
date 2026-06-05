# SupportOps AI Diagnostic API - Backend

FastAPI backend for a support operations diagnostic platform. The API runs network diagnostic checks, stores diagnostic and ticket records, creates troubleshooting insights, and keeps saved insight history for review.

## Project Purpose

This backend demonstrates practical backend engineering for IT support workflows:

- API design with FastAPI
- diagnostic workflow automation
- persistent support ticket operations
- database-backed diagnostic and ticket history
- public target validation
- troubleshooting insight generation
- sensitive-text redaction before external AI calls
- request rate limiting for insight endpoints
- automated backend testing
- deployment-aware error handling

The backend is paired with a React/Vite frontend deployed on Vercel.

Frontend:

```text
https://it-support-diagnostic-portal.vercel.app
```

Backend API docs:

```text
https://it-support-api-g0b4.onrender.com/docs
```

## Tech Stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite for local development
- Uvicorn
- httpx
- Pytest
- GitHub Actions
- Render

## Core Features

- Public domain/IP diagnostic checks
- DNS resolution
- Ping or TCP reachability fallback
- Traceroute or deployment-safe fallback messaging
- Common port checks for 21, 22, 80, 443, and 3389
- Persistent diagnostic history
- Persistent support ticket creation
- Ticket status updates
- Ticket priority handling
- Ticket filtering by status, priority, and search
- Ticket analytics endpoint
- Troubleshooting insight generation
- Saved insight history
- Sensitive-text redaction before AI prompt generation
- Basic request rate limiting for insight endpoints
- Health check endpoint for deployment monitoring

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
  "diagnostic_id": 1,
  "timestamp": "2026-06-05T00:00:00",
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

### Diagnostic History

```http
GET /api/diagnostics/history
```

Returns recent diagnostic runs.

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
  "traceroute_data": "Route diagnostic output here",
  "priority": "medium"
}
```

Example response structure:

```json
{
  "status": "success",
  "message": "Ticket TKT-20260605123456000000 successfully created.",
  "ticket_id": "TKT-20260605123456000000",
  "data_logged": {
    "user": "Demo Agent",
    "issue_target": "google.com"
  }
}
```

### List Tickets

```http
GET /api/tickets
```

Supported query parameters:

```text
status=open
priority=medium
search=google
limit=50
```

### Ticket Detail

```http
GET /api/tickets/{ticket_id}
```

Returns a single ticket by ticket number.

### Update Ticket Status

```http
PATCH /api/tickets/{ticket_id}
```

Example request:

```json
{
  "status": "in_progress"
}
```

Allowed statuses:

```text
open
in_progress
resolved
closed
```

### Ticket Analytics

```http
GET /api/tickets/analytics
```

Returns ticket totals by status and priority.

### Generate Insight

```http
POST /api/ai/insight
```

Example request:

```json
{
  "target": "google.com",
  "ping_data": "Reachability output here",
  "traceroute_data": "Route diagnostic output here",
  "ports": {
    "80": "Open",
    "443": "Open"
  }
}
```

Example response structure:

```json
{
  "target": "google.com",
  "insight": {
    "provider": "local_rules",
    "summary": "Diagnostics were reviewed for google.com.",
    "risk_level": "low",
    "probable_causes": [
      "The target may be reachable if common web ports are open."
    ],
    "recommended_next_steps": [
      "Confirm the target value is correct."
    ]
  }
}
```

When `OPENAI_API_KEY` is not configured, the endpoint returns a local rules-based fallback. This keeps local development and demos working without requiring an external provider.

### Save Insight

```http
POST /api/ai/insight/save
```

Generates and stores an insight record. The record can optionally be linked to a ticket.

Example request:

```json
{
  "ticket_id": "TKT-20260605123456000000",
  "target": "google.com",
  "ping_data": "Reachability output here",
  "traceroute_data": "Route diagnostic output here",
  "ports": {
    "80": "Open",
    "443": "Open"
  }
}
```

### List Saved Insights

```http
GET /api/ai/insights
```

Supported query parameters:

```text
ticket_id=TKT-20260605123456000000
limit=25
```

## Safety and Validation

The backend validates diagnostic targets before running diagnostics or saving insight records. Localhost, private network addresses, reserved IP ranges, malformed URLs, and internal targets are blocked.

Insight requests include:

- sensitive text redaction before prompt generation
- email, API key, token, password, credentialed URL, and long-ID redaction
- response normalization
- basic in-memory rate limiting
- fallback behavior when the external provider is unavailable or not configured

## Cloud Deployment Behavior

Some hosted server environments do not provide system-level commands like `ping` or `traceroute`.

Instead of returning raw server errors, this backend handles those cases gracefully:

- If `ping` is unavailable, the API runs a TCP reachability check.
- If `traceroute` is unavailable, the API returns a clean explanation.
- DNS resolution and port checks still work.

This keeps the deployed app stable in local and hosted environments.

## Environment Variables

Create a local `.env` file or configure variables in the deployment platform.

```text
ALLOWED_ORIGINS=http://localhost:5173,https://it-support-diagnostic-portal.vercel.app
DATABASE_URL=sqlite:///./supportops.db
OPENAI_API_KEY=
AI_MODEL=
```

Notes:

- Keep real API keys out of git.
- Use `.env.example` as the safe template.
- If `OPENAI_API_KEY` is empty, insight endpoints use local fallback logic.

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

Local API docs:

```text
http://127.0.0.1:8000/docs
```

## Testing

Run all backend tests:

```bash
pytest
```

Run Python compile checks:

```bash
python -m py_compile app/api/ai.py
python -m py_compile app/api/diagnostics.py
python -m py_compile app/api/tickets.py
python -m py_compile app/core/config.py
python -m py_compile app/db/database.py
python -m py_compile app/db/models.py
python -m py_compile app/models/schemas.py
python -m py_compile app/services/ai_insights.py
python -m py_compile app/services/network_tools.py
python -m py_compile app/services/rate_limit.py
python -m py_compile app/services/redaction.py
python -m py_compile app/services/target_validation.py
```

Current automated coverage includes:

- health checks
- diagnostic endpoint behavior
- target validation
- persistent ticket creation
- ticket listing and filtering
- ticket status updates
- ticket analytics
- insight fallback behavior
- saved insight history
- redaction behavior
- rate-limit helper behavior

## Repository Pair

Frontend repo:

```text
AC0731/it-helpdesk-frontend
```

Backend repo:

```text
AC0731/it-helpdesk-backend
```

## Author

Akanksha Chavda  
GitHub: AC0731
