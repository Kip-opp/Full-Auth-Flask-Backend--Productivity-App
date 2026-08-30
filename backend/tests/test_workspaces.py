"""Workspace route tests."""
import json
import pytest

from tests.conftest import auth_headers


def test_workspace_crud(auth_client):
    client, token, _ = auth_client
    # Create
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'My Notebook', 'description': 'first'},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    ws = json.loads(response.data)['data']
    assert ws['name'] == 'My Notebook'

    # List
    response = client.get('/api/v1/workspaces', headers=auth_headers(token))
    assert response.status_code == 200
    assert len(json.loads(response.data)['data']['items']) == 1

    # Update
    response = client.patch(
        f'/api/v1/workspaces/{ws["id"]}',
        json={'name': 'Updated'},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert json.loads(response.data)['data']['name'] == 'Updated'

    # Delete
    response = client.delete(
        f'/api/v1/workspaces/{ws["id"]}', headers=auth_headers(token)
    )
    assert response.status_code == 200

    response = client.get(
        f'/api/v1/workspaces/{ws["id"]}', headers=auth_headers(token)
    )
    assert response.status_code == 404


def test_cross_user_workspace_returns_404(client, app, two_users):
    # Alice creates a workspace.
    response = client.post('/api/auth/login', json={
        'username': 'alice', 'password': 'password123'
    })
    alice_token = json.loads(response.data)['data']['token']
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'Alice WS'},
        headers=auth_headers(alice_token),
    )
    ws_id = json.loads(response.data)['data']['id']

    # Bob cannot read or mutate it.
    response = client.post('/api/auth/login', json={
        'username': 'bob', 'password': 'password123'
    })
    bob_token = json.loads(response.data)['data']['token']
    for method, url in [
        ('GET', f'/api/v1/workspaces/{ws_id}'),
        ('PATCH', f'/api/v1/workspaces/{ws_id}'),
        ('DELETE', f'/api/v1/workspaces/{ws_id}'),
    ]:
        response = getattr(client, method.lower())(
            url, headers=auth_headers(bob_token),
            json={'name': 'hijack'},
        )
        assert response.status_code == 404, (method, url, response.status_code)
