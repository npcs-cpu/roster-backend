# Roster SaaS Phase 1 Backend

Phase 1 backend for ingesting one CrewConnex calendar feed, normalizing current + next month events, and serving month/day calendar APIs.

## Stack
- FastAPI
- SQLAlchemy 2.x
- MariaDB via PyMySQL
- Fernet encryption for feed URLs
- HTTPX for ICS download
- iCalendar parser

## Setup

1. Create a MariaDB database named `roster_app`.
2. Create a virtualenv and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Generate a Fernet key:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
4. Copy `.env.example` to `.env` and fill in values.
5. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```

## First sync
```bash
curl -X POST "http://localhost:8000/api/admin/crew/10213/sync" \
  -H "Content-Type: application/json" \
  -d '{"feed_url":"https://nbtweb3.pdc.com/pdccrewcalendar/REPLACE_ME"}'
```

## Test endpoints
```bash
curl "http://localhost:8000/api/calendar/month?year=2026&month=4"
curl "http://localhost:8000/api/calendar/day?date=2026-04-22"
```

## Notes
- `webcal://` and `webcals://` links are normalized to `https://` automatically.
- Phase 1 currently assumes all crew are in JFK base and uses `America/New_York` for local date grouping.
- Tables are auto-created on startup for convenience. In production, switch to Alembic migrations.
