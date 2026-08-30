# Vercel deployment

This repository is configured to deploy the full monorepo to [Vercel](https://vercel.com):

- The static frontend in `client-with-jwt/` is served at `/`.
- The Flask backend in `backend/` is exposed under `/api/*` as a Python serverless function.

## One-time setup

1. Install the Vercel CLI and log in:
   ```bash
   npm i -g vercel
   vercel login
   ```
2. From the repository root, link the project (first deploy) and link it to a Postgres database later:
   ```bash
   vercel
   vercel link
   ```

## Required environment variables

Set these in the Vercel project settings (or via `vercel env add`):

| Variable | Purpose | Example |
| --- | --- | --- |
| `SECRET_KEY` | Flask session signing | 32+ random characters |
| `JWT_SECRET_KEY` | JWT signing | 32+ random characters |
| `DATABASE_URL` or `SQLALCHEMY_DATABASE_URI` | Hosted Postgres URL | `postgresql+psycopg2://user:pass@host:5432/db` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `https://your-app.vercel.app` |

Vercel provides a hosted Postgres option under the Storage tab; the
resulting `DATABASE_URL` is injected automatically.

## Database migrations

Vercel does not run `flask db upgrade` automatically. Run migrations
locally against the production database before deploying, or run them
from a one-off job:

```bash
DATABASE_URL=<your-postgres-url> \
FLASK_APP=backend/run.py \
pipenv run flask db upgrade
```

The P0 item "migration-only production startup" from the developer
roadmap should replace this manual step.

## What does not work on Vercel

- The local `flask process-jobs` worker. The roadmap calls for moving
  jobs to a hosted queue (e.g. Celery + Redis, or Upstash QStash).
- File-based SQLite. A hosted Postgres (or any SQLAlchemy-compatible
  URL) is required.
- Google OAuth. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in
  the Vercel project env; the `/api/auth/google/*` routes will pick
  them up.

## Deploy

```bash
vercel        # preview deployment
vercel --prod # production deployment
```
