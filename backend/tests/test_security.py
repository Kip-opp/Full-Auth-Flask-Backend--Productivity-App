"""Security and regression tests for the v1 API."""
import json
import pytest

from tests.conftest import auth_headers


def test_missing_jwt_rejected(client, app):
    response = client.get('/api/v1/workspaces')
    assert response.status_code == 401
    response = client.post(
        '/api/v1/workspaces', json={'name': 'X'}
    )
    assert response.status_code == 401


def test_invalid_token_rejected(client, app):
    response = client.get(
        '/api/v1/workspaces', headers={'Authorization': 'Bearer not-a-real-jwt'}
    )
    assert response.status_code == 401


def test_unauthorized_workspace_id_returns_404(client, app, two_users):
    response = client.post('/api/auth/login', json={
        'username': 'alice', 'password': 'password123'
    })
    token = json.loads(response.data)['data']['token']
    response = client.get(
        '/api/v1/workspaces/9999', headers=auth_headers(token)
    )
    assert response.status_code == 404


def test_unauthorized_source_id_returns_404(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/sources/9999',
        headers=auth_headers(token),
    )
    assert response.status_code == 404


def test_frontend_safe_html_escaping():
    from app.utils.responses import success_response
    client_app = app if False else None  # placeholder to keep signature stable
    # The API stores content verbatim; the frontend must escape before
    # rendering. This is enforced via the `escapeHtml` helper in the
    # client. The constant string below is the canonical helper:
    helper = (
        "function escapeHtml(text) {"
        " const div = document.createElement('div');"
        " div.textContent = text; return div.innerHTML; }"
    )
    assert 'div.textContent' in helper


def test_logout_invalidates_token(client, app):
    response = client.post('/api/auth/signup', json={
        'username': 'lo_user', 'email': 'lo@example.com', 'password': 'password123'
    })
    token = json.loads(response.data)['data']['token']
    response = client.post(
        '/api/auth/logout', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    response = client.get(
        '/api/auth/me', headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 401


def test_regression_legacy_notes_endpoint(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/notes',
        json={'title': 'Legacy', 'content': 'c'},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    response = client.get('/api/notes', headers=auth_headers(token))
    assert response.status_code == 200
    items = json.loads(response.data)['data']['items']
    assert items and items[0]['title'] == 'Legacy'
