#!/usr/bin/env bash
# Backend-only smoke collection.
# Exercises the versioned API end-to-end without a browser. Intended for
# `bash` 4+ and `curl`. Fails on the first non-2xx response.
#
# Usage:
#   API=http://localhost:5000 ./api/collections/curl/smoke.sh
#
# Optional env:
#   EMAIL, PASSWORD, USERNAME  account to create / log in as
#   WORKSPACE_NAME             workspace name (default: "API smoke notebook")
set -euo pipefail

API=${API:-http://localhost:5000}
EMAIL=${EMAIL:-smoke-$(date +%s)@example.com}
PASSWORD=${PASSWORD:-password123}
USERNAME=${USERNAME:-smoke-$(date +%s)}
WORKSPACE_NAME=${WORKSPACE_NAME:-API smoke notebook}

red()   { printf "\033[31m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
blue()  { printf "\033[34m%s\033[0m\n" "$*"; }

redact() { sed -E 's/(Bearer )[^"]+/\1<redacted>/g'; }

call() {
  local method=$1 url=$2
  shift 2
  local response status
  response=$(curl -sS -o /tmp/smoke.body -w "%{http_code}" -X "$method" "$url" "$@" || true)
  status=$response
  if [[ ! $status =~ ^2 ]]; then
    red "FAIL: $method $url -> $status"
    red "Body: $(cat /tmp/smoke.body)"
    exit 1
  fi
  cat /tmp/smoke.body
}

# 1. Health
blue "==> health"
call GET "$API/api/health" >/dev/null

# 2. Signup (or login if 409)
blue "==> signup"
signup_body=$(curl -sS -o /tmp/smoke.body -w "%{http_code}" -X POST "$API/api/auth/signup" \
  -H 'Content-Type: application/json' \
  -d "{\"username\":\"$USERNAME\",\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" || true)
case "$signup_body" in
  2*) ;;
  409) ;;
  *) red "signup failed: $signup_body"; cat /tmp/smoke.body; exit 1;;
esac

blue "==> login"
TOKEN=$(call POST "$API/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["token"])')

AUTH=(-H "Authorization: Bearer $TOKEN")

# 3. Workspace
blue "==> create workspace"
WORKSPACE_ID=$(call POST "$API/api/v1/workspaces" "${AUTH[@]}" \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"$WORKSPACE_NAME\",\"description\":\"Smoke test workspace\"}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["id"])')

# 4. Notebook note
blue "==> create notebook note"
call POST "$API/api/v1/workspaces/$WORKSPACE_ID/notes" "${AUTH[@]}" \
  -H 'Content-Type: application/json' \
  -d '{"title":"Architecture decision","content":"Use durable jobs."}' >/dev/null

# 5. Notebook question
blue "==> create question"
call POST "$API/api/v1/workspaces/$WORKSPACE_ID/queries" "${AUTH[@]}" \
  -H 'Content-Type: application/json' \
  -d '{"question":"Why use durable jobs?"}' >/dev/null

# 6. List queries
blue "==> list queries"
call GET "$API/api/v1/workspaces/$WORKSPACE_ID/queries" "${AUTH[@]}" >/dev/null

green "smoke OK: workspace=$WORKSPACE_ID token=<redacted>"
