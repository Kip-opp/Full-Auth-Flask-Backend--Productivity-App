# Notebook Workspace

A source-grounded notebook workspace layered on top of the existing
Flask authentication and notes application. Import HTTP(S) sources,
write workspace notes, generate slides, mind maps, data tables, quizzes,
and summaries, and ask the notebook questions grounded in your
evidence.

## Features

- **Workspaces** owned by a single user.
- **Sources**: HTTP(S) URL ingestion with SSRF guards, content hashing,
  and versioned document storage.
- **Notebook notes** that are searchable by the Q&A service.
- **Ask notebook**: grounded question answering with citations.
- **Generation**: slides, mind map, data table, quiz, and summary
  artifacts produced behind a replaceable provider interface.
- **Async jobs**: HTTP requests create durable `GenerationJob` records
  processed by a separate worker.
- **Legacy notes and authentication** are preserved.

## Quick start

```bash
cd backend
pipenv install
pipenv run flask db upgrade
pipenv run python seed.py          # optional
pipenv run python run.py           # serves the API on :5000
# In another shell, run the worker:
pipenv run flask worker --limit 25
```

Serve the static client on `:3000` (e.g. `python -m http.server 3000`
from `client-with-jwt/`).

## Configuration

See `backend/.env.example` for the full list. Important variables:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Flask session secret. |
| `JWT_SECRET_KEY` | JWT signing secret. |
| `SQLALCHEMY_DATABASE_URI` | Database URL. SQLite by default. |
| `CORS_ORIGINS` | Comma-separated allowed origins. |
| `ARTIFACT_PROVIDER` | Future: name of the artifact provider to load. |
| `QA_PROVIDER` | Future: name of the Q&A provider to load. |

The MVP uses local deterministic providers; no provider credentials are
required. Production deployments should set provider credentials via
environment variables and run the worker in a separate process.

## API quick reference

```
POST   /api/auth/signup
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

GET    /api/notes
POST   /api/notes
GET    /api/notes/:id
PATCH  /api/notes/:id
DELETE /api/notes/:id

GET    /api/v1/workspaces
POST   /api/v1/workspaces
GET    /api/v1/workspaces/:id
PATCH  /api/v1/workspaces/:id
DELETE /api/v1/workspaces/:id

GET    /api/v1/workspaces/:id/sources
POST   /api/v1/workspaces/:id/sources
GET    /api/v1/workspaces/:id/sources/:source_id
DELETE /api/v1/workspaces/:id/sources/:source_id
POST   /api/v1/workspaces/:id/sources/:source_id/sync

GET    /api/v1/workspaces/:id/artifacts
POST   /api/v1/workspaces/:id/artifacts
GET    /api/v1/workspaces/:id/artifacts/:artifact_id

GET    /api/v1/workspaces/:id/notes
POST   /api/v1/workspaces/:id/notes
PATCH  /api/v1/workspaces/:id/notes/:note_id
DELETE /api/v1/workspaces/:id/notes/:note_id

GET    /api/v1/workspaces/:id/queries
POST   /api/v1/workspaces/:id/queries
GET    /api/v1/workspaces/:id/queries/:query_id

GET    /api/v1/jobs/:job_id
POST   /api/v1/jobs/:job_id/run
```

## Tests

```bash
cd backend
pipenv run pytest
```

The suite covers workspace, source, ingestion, artifact, job lifecycle,
Q&A, security, and legacy regression cases.

## Visual validation notes

The current build was smoke-tested locally with the backend on port
5000 and the static client on port 3000. Verified states:

- Authentication screen loads the redesigned Notebook sign-in flow with
  no frontend parse errors.
- Desktop dashboard renders a dark sidebar, grouped navigation,
  workspace switcher, hero, metrics, artifact launchers, and a
  private-by-default card.
- Ask notebook shows the question composer, optional source/note
  selectors, recent conversation, and empty state.
- Sources screen shows the URL/title form and a queue explanation.
- Notebook notes screen shows the title/content editor and searchable
  note list.
- Mobile stylesheet collapses the sidebar into a drawer with backdrop
  and stacks forms and cards at narrow widths.

The redesign intentionally uses the existing dependency-free frontend
and preserves the legacy Notes/Archived navigation. The local Q&A and
artifact providers remain functional through the existing API and
worker boundaries; visual changes do not alter backend contracts.
