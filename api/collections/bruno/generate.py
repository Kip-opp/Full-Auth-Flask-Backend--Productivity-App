#!/usr/bin/env python3
"""Generate Bruno (.bru) request files for the Notebook Workspace API.

This script is idempotent. Run it after editing api/openapi.yaml to keep
the checked-in Bruno collection in sync. The OpenAPI document is the
source of truth; the Bruno collection is generated from it.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OPENAPI = ROOT / "api" / "openapi.yaml"
OUT = ROOT / "api" / "collections" / "bruno" / "notebook-workspace"


def block(name: str, value) -> str:
    if value is None or value == "":
        return ""
    body = textwrap.dedent(str(value)).strip("\n")
    return f"{name} {{\n{body}\n}}\n\n"


def examples(schema: dict) -> dict:
    if not isinstance(schema, dict):
        return {}
    if "example" in schema:
        return {"example": schema["example"]}
    return {}


def render_body(path_item: dict) -> str | None:
    """Return a JSON example body or None for requests without one."""
    post = path_item.get("post")
    if not post:
        return None
    rb = post.get("requestBody")
    if not rb:
        return None
    content = rb.get("content", {}).get("application/json", {})
    sch = content.get("schema", {})
    # Build a small example using OpenAPI required + types.
    return _example_from_schema(sch)


def _example_from_schema(schema: dict) -> str:
    if "$ref" in schema:
        # Examples for refs are kept tiny and obviously placeholder.
        ref = schema["$ref"].rsplit("/", 1)[-1]
        return _EXAMPLE_BODIES.get(ref, "{}")
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        out = {}
        for name, sub in props.items():
            if name in required or len(out) < 4:
                out[name] = _example_value(sub, name)
        return _import_json(out)
    if t == "array":
        return "[]"
    return "null"


def _example_value(sub: dict, name: str) -> object:
    if "example" in sub:
        return sub["example"]
    if "$ref" in sub:
        return _EXAMPLE_REFS.get(sub["$ref"].rsplit("/", 1)[-1], f"<{name}>")
    enum = sub.get("enum")
    if enum:
        return enum[0]
    t = sub.get("type")
    if t == "string":
        if sub.get("format") == "uri":
            return "https://example.com/article"
        if sub.get("format") == "email":
            return "user@example.com"
        if sub.get("format") == "date-time":
            return "2026-01-01T00:00:00Z"
        if sub.get("format") == "jwt":
            return "<jwt>"
        return f"example {name}"
    if t == "integer":
        return 1
    if t == "boolean":
        return True
    if t == "array":
        return []
    if t == "object" or "properties" in sub:
        return _example_from_schema(sub)
    return None


def _import_json(obj) -> str:
    import json
    return json.dumps(obj, indent=2)


_EXAMPLE_REFS = {
    "User": {"id": 1, "username": "alice", "email": "alice@example.com"},
    "Workspace": {"id": 1, "name": "API development notebook"},
    "Source": {"id": 1, "url": "https://example.com/article"},
    "Artifact": {"id": 1, "artifact_type": "summary", "title": "Summary"},
    "WorkspaceNote": {"id": 1, "title": "Architecture decision"},
    "Query": {"id": 1, "question": "Why use durable jobs?"},
    "Job": {"id": 1, "job_type": "source_ingestion", "status": "queued"},
}

_EXAMPLE_BODIES = {
    "SignupRequest": _import_json(
        {"username": "alice", "email": "alice@example.com", "password": "password123"}
    ),
    "LoginRequest": _import_json({"identifier": "alice", "password": "password123"}),
    "WorkspaceCreateRequest": _import_json(
        {"name": "API development notebook", "description": "Backend-only smoke test"}
    ),
    "WorkspaceUpdateRequest": _import_json({"name": "Renamed notebook"}),
    "SourceCreateRequest": _import_json(
        {"url": "https://example.com/article", "title": "Example article"}
    ),
    "ArtifactCreateRequest": _import_json(
        {
            "artifact_type": "summary",
            "title": "Workspace summary",
            "instructions": "Summarize the workspace sources",
            "source_ids": [],
        }
    ),
    "WorkspaceNoteCreateRequest": _import_json(
        {"title": "Architecture decision", "content": "Use durable jobs."}
    ),
    "WorkspaceNoteUpdateRequest": _import_json({"status": "archived"}),
    "QueryCreateRequest": _import_json(
        {
            "question": "Why should ingestion and AI generation use durable jobs?",
            "source_ids": [],
            "note_ids": [],
        }
    ),
    "NoteCreateRequest": _import_json(
        {"title": "My note", "content": "Note content", "status": "active"}
    ),
    "NoteUpdateRequest": _import_json({"status": "archived"}),
}


def path_to_folder(path: str) -> str:
    parts = [p for p in path.split("/") if p and not p.startswith("{")]
    if not parts:
        return "Misc"
    # group /api/v1/workspaces/X/... under "Workspaces"
    if "workspaces" in parts:
        idx = parts.index("workspaces")
        suffix = "/".join(parts[idx + 1 :]) or "root"
        return f"Workspaces/{suffix}"
    if "notes" in parts and "v1" not in parts:
        return "Notes (legacy)"
    if "artifacts" in parts:
        return "Artifacts"
    if "sources" in parts:
        return "Sources"
    if "queries" in parts:
        return "Queries"
    if "jobs" in parts:
        return "Jobs"
    if "auth" in parts:
        return "Auth"
    return parts[0].title()


def to_bru_filename(method: str, path: str) -> str:
    safe = path.strip("/").replace("/", "-").replace("{", "").replace("}", "")
    return f"{method.upper()} {safe}.bru"


def render_bru(method: str, path: str, op: dict, params_in_path: list[str]) -> str:
    name = op.get("summary", f"{method.upper()} {path}")
    out = block("meta", {"type": "http", "name": name, "seq": 0})
    out += block("vars", {"token": "{{token}}"})
    auth_scheme = op.get("security")
    if auth_scheme and "bearerAuth" in (next(iter(s) for s in auth_scheme) if auth_scheme else {}):
        out += block("auth", {"bearer": {"token": "{{token}}"}})

    url = "{{base_url}}" + path
    for p in params_in_path:
        url = url.replace("{" + p + "}", "{{" + p + "}}")

    if method in ("get", "delete"):
        out += f"{{{{\n  method: {method.upper()}\n  url: {url}\n}}}}\n\n"
        return out

    # POST / PATCH bodies
    rb = op.get("requestBody")
    body = None
    if rb:
        content = rb.get("content", {}).get("application/json", {})
        sch = content.get("schema", {})
        body = _example_from_schema(sch)

    out += f"{{{{\n  method: {method.upper()}\n  url: {url}\n"
    if body is not None:
        out += "  body: json\n"
        out += "}\n\n"
        out += "body:json {\n"
        out += textwrap.indent(body, "  ")
        out += "\n}\n"
    else:
        out += "}\n\n"
    return out


def main() -> int:
    spec = yaml.safe_load(OPENAPI.read_text())
    paths = spec.get("paths", {})

    # Track generated files so we can prune folders that no longer exist.
    generated: set[Path] = set()

    for path, item in paths.items():
        params_in_path = [
            p["name"]
            for p in item.get("parameters", [])
            if p.get("in") == "path"
        ]
        for method in ("get", "post", "patch", "delete", "put"):
            op = item.get(method)
            if not op:
                continue
            folder = path_to_folder(path)
            folder_path = OUT / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            target = folder_path / to_bru_filename(method, path)
            target.write_text(render_bru(method, path, op, params_in_path))
            generated.add(target)

    # Prune any stale .bru files we no longer generate.
    for bru in OUT.rglob("*.bru"):
        if bru not in generated:
            bru.unlink()
    # Remove empty directories.
    for d in sorted([p for p in OUT.rglob("*") if p.is_dir()], reverse=True):
        if d == OUT:
            continue
        if not any(d.iterdir()):
            d.rmdir()

    print(f"Generated {len(generated)} Bruno requests under {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
