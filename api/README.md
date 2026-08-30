# API contracts

This directory is the **frontend-independent** source of truth for the
Notebook Workspace HTTP API.

| File | Purpose |
| --- | --- |
| `openapi.yaml` | OpenAPI 3.0.3 document. Every versioned route has request, response, auth, error, and status-code documentation. |
| `collections/bruno/` | Bruno collection generated from `openapi.yaml` (run `python api/collections/bruno/generate.py` to refresh). |
| `collections/curl/smoke.sh` | Bash + curl smoke flow that runs without a browser. Exits non-zero on any non-2xx response. |

## Regenerating the Bruno collection

```bash
pip install pyyaml
python api/collections/bruno/generate.py
```

The Bruno environment template lives at
`api/collections/bruno/notebook-workspace/environments/Local.bru`. Set
`token` after the first `POST /api/auth/login` and reuse it for every
protected request.

## Running the smoke flow

```bash
# from repo root, with the backend running on :5000
API=http://localhost:5000 bash api/collections/curl/smoke.sh
```

The script intentionally avoids printing the JWT to stdout.

## Versioning policy

- New routes go under `/api/v1/*`. The legacy `/api/auth/*` and
  `/api/notes/*` contracts remain unchanged.
- When a route shape changes, update `openapi.yaml` first, regenerate
  the Bruno collection, then update the backend.
- Error responses always use the standard envelope:
  `{ "success": false, "error": { "code": "...", "message": "...", "details": ... } }`.
