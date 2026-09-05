# Architecture

This document describes the source-grounded Notebook workspace layered on
top of the existing Flask authentication and notes application. The legacy
`/api/auth/*` and `/api/notes/*` contracts are preserved; private workspace
capabilities live under `/api/v1/*` and the curated read-only demo lives under
`/api/demo/workspace`.

## Goals

- Every workspace, source, note, artifact, query, and job is owned by one
  user and is unreachable from another user's session.
- HTTP requests create or read durable jobs; expensive work is executed by
  a separate worker process.
- Provider calls live behind a stable interface. The local provider
  returns deterministic, extractive output so the API and UI work without
  external credentials. A real model adapter (OpenAI, Anthropic, etc.) is
  expected to implement the same protocol.
- Sources are normalized, versioned, and content-hashed so re-ingestion
  is idempotent.
- The notebook can be asked questions over the workspace's ready sources
  and active notes. Answers are grounded in evidence and carry
  citations.

## Layers

```
client-with-jwt/         Static JS client (no build step)
  js/api.js               Centralized HTTP wrapper
  js/auth.js              Authentication + dashboard shell
  js/workspace.js         Workspace UI pages
  css/workspace.css       Visual system for the workspace shell

backend/
  app/
    __init__.py           Application factory; registers blueprints and CLI
    config.py             Environment-driven configuration
    extensions.py         Flask extensions (db, migrate, bcrypt)
    models/               SQLAlchemy models, one per bounded context
    routes/               HTTP layer: parse, call service, respond
    schemas/              Marshmallow validation at the boundary
    services/             Business logic, providers, worker
    cli/                  Flask CLI commands (worker)
    utils/                Shared helpers (responses, decorators)
  migrations/             Alembic revisions
  tests/                  Pytest suite
```

## Domain model

| Model | Purpose |
| --- | --- |
| `Workspace` | Top-level tenant container owned by a user. |
| `Source` | A URL imported into a workspace. Carries status, content hash, error. |
| `Document` | A single ingested snapshot of a source. Re-syncs create new versions. |
| `DocumentChunk` | Deterministic character-windowed chunks used for retrieval. |
| `Artifact` | A generated deliverable (slides, mindmap, table, quiz, summary). |
| `ArtifactSource` | Join table linking artifacts to the sources used as evidence. |
| `GenerationJob` | A durable, auditable unit of work. `source_ingestion`, `artifact_generation`, `question_answering`. |
| `WorkspaceNote` | A notebook note written inside a workspace; archived notes are excluded from default retrieval. |
| `Query` | A user question, its grounded answer, citations, and the linked `GenerationJob`. |

## HTTP API

The standard envelope is `{success, message, data}` on success and
`{success, error: {code, message, details?}}` on failure. New endpoints
are versioned under `/api/v1`.

Unauthenticated visitors receive a fixed demo snapshot from
`GET /api/demo/workspace`. It is not backed by a user-owned workspace and
cannot be used to read arbitrary IDs. The client keeps the demo read-only;
sign-in is required for notes, source ingestion, questions, and generation.

| Method | Endpoint | Notes |
| --- | --- | --- |
| GET / POST | `/api/v1/workspaces` | List or create a workspace |
| GET / PATCH / DELETE | `/api/v1/workspaces/:id` | Manage one owned workspace |
| GET / POST | `/api/v1/workspaces/:id/sources` | List or queue URL ingestion |
| GET / DELETE | `/api/v1/workspaces/:id/sources/:source_id` | Inspect or delete |
| POST | `/api/v1/workspaces/:id/sources/:source_id/sync` | Re-sync |
| GET / POST | `/api/v1/workspaces/:id/artifacts` | List or queue artifact |
| GET | `/api/v1/workspaces/:id/artifacts/:artifact_id` | Read content |
| GET / POST | `/api/v1/workspaces/:id/notes` | Notebook notes |
| PATCH / DELETE | `/api/v1/workspaces/:id/notes/:note_id` | Update / archive / delete |
| GET / POST | `/api/v1/workspaces/:id/queries` | List or queue question |
| GET | `/api/v1/workspaces/:id/queries/:query_id` | Read answer + citations |
| GET | `/api/v1/jobs/:job_id` | Poll job status |
| POST | `/api/v1/jobs/:job_id/run` | Local-only execution hook |

The legacy `/api/auth/*` and `/api/notes/*` routes remain unchanged and
continue to work; the new endpoints are additive.

## Provider boundary

```python
class ArtifactProvider(Protocol):
    def generate(self, artifact_type, title, instructions, evidence): ...
```

```python
class QuestionAnswerProvider(Protocol):
    def answer(self, question, evidence): ...
```

`LocalArtifactProvider` and `LocalQuestionAnswerProvider` ship with the
repository and are used in development. They are deliberately
deterministic so the API and UI behave predictably without secrets.
Production adapters must:

1. Receive only the tenant-authorized evidence.
2. Treat source text as untrusted data; application policies outrank
   any instructions in the source.
3. Emit structured JSON; do not require the frontend to parse prose.
4. Attach source IDs / locators to every claim; never invent URLs or IDs.
5. Set timeouts and retry only transient failures.
6. Never log credentials or sensitive content.

## Source ingestion and SSRF

The default fetcher lives in `services/source_service.py` and is
replaceable. URL validation is enforced before any fetch:

- Scheme must be `http` or `https`.
- Host must resolve to a public IP. Loopback, link-local, private,
  reserved, and multicast ranges are refused.
- `localhost`, embedded credentials, and `file:` URLs are refused.
- Responses are capped at 2 MiB and the fetch times out after 10s.

> **MVP only.** The in-process fetcher is convenient for local
> development. Production deployments must route fetches through an
> egress proxy or a dedicated crawler service that enforces the same
> rules and adds redirect policy, content-type restrictions, and
> per-tenant rate limits.

## Asynchronous boundary

HTTP requests create `GenerationJob` records and return immediately.
The worker (`flask worker --workspace-id N --limit 25`) processes a
bounded batch of queued jobs and updates the job state. The local
client may also call `POST /api/v1/jobs/:id/run` to advance a single
job in development. A production worker should use atomic claiming,
visibility timeouts, dead-letter handling, and per-user concurrency
limits; the worker module is intentionally small so it can be replaced.

## Idempotency

- Re-running a `source_ingestion` job on the same content hash is a
  no-op (no new document version, no new chunks).
- Re-running a `succeeded` artifact or query job is a no-op.
- A failed job is re-runnable up to `max_attempts`. Exceeding the
  budget transitions the job to `failed` with a bounded error message.

## Q&A retrieval

`backend/app/services/query_service.py` exposes a replaceable retrieval
function that:

1. Loads only `Source` rows that belong to the workspace and are
   `ready`, plus the latest `Document` and ordered `DocumentChunk`
   rows.
2. Loads only `WorkspaceNote` rows in the workspace with status
   `active`.
3. Ranks evidence by a deterministic lexical score with a stable
   limit.
4. Returns evidence objects with `kind`, `source_id` or `note_id`,
   `title`, `locator`, and `excerpt`.
5. Passes only those evidence objects to the provider.
6. Persists the selected evidence scope and citations on `Query`.

A production adapter should swap lexical ranking for hybrid BM25 +
vector retrieval while keeping the workspace filter, evidence
provenance, and citation mapping.

## Security

- All v1 routes require a JWT (`Authorization: Bearer <token>`).
- Cross-user and cross-workspace IDs return `404`.
- All user-supplied text is escaped on the client (`escapeHtml`,
  `escapeAttr`) before rendering.
- External links carry `rel="noopener noreferrer"` and `target="_blank"`.
- Model-provider SDKs are not used inside request handlers; they live
  in provider modules loaded by the worker.

## Future prompts

When continuing the implementation, ask the next agent to complete
exactly one bounded slice. Suggested next slices:

- "Add PostgreSQL migrations and a Redis-backed job adapter without
  changing the API contract."
- "Add hybrid BM25 + vector retrieval and citation validation for quiz
  generation."
- "Add workspace members and role-based authorization with regression
  tests."
