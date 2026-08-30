"""Q&A route and service tests."""
import json
import pytest

from app.extensions import db
from app.models.job import GenerationJob
from app.models.notebook import Query, WorkspaceNote
from app.services.query_service import run_query_job
from tests.conftest import auth_headers


def test_workspace_note_crud(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']

    # Create
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/notes',
        json={'title': 'T', 'content': 'C'},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    note = json.loads(response.data)['data']

    # Update
    response = client.patch(
        f'/api/v1/workspaces/{ws_id}/notes/{note["id"]}',
        json={'content': 'updated'},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert json.loads(response.data)['data']['content'] == 'updated'

    # Archive
    response = client.patch(
        f'/api/v1/workspaces/{ws_id}/notes/{note["id"]}',
        json={'status': 'archived'},
        headers=auth_headers(token),
    )
    assert response.status_code == 200

    # Default list excludes archived
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/notes', headers=auth_headers(token)
    )
    assert json.loads(response.data)['data']['items'] == []

    # include_archived=true
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/notes?include_archived=true',
        headers=auth_headers(token),
    )
    assert len(json.loads(response.data)['data']['items']) == 1

    # Delete
    response = client.delete(
        f'/api/v1/workspaces/{ws_id}/notes/{note["id"]}',
        headers=auth_headers(token),
    )
    assert response.status_code == 200


def test_query_retrieves_source_chunk(client, app, auth_client, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'What does photosynthesis do?'},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    payload = json.loads(response.data)['data']
    job = payload['job']
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    body = json.loads(response.data)
    assert body['data']['status'] == GenerationJob.SUCCEEDED
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/queries/{payload["query"]["id"]}',
        headers=auth_headers(token),
    )
    result = json.loads(response.data)['data']
    assert result['status'] == Query.SUCCEEDED
    assert result['citations']
    citation = result['citations'][0]
    assert citation['source_id'] == ready_source


def test_query_mixed_evidence(client, app, auth_client, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/notes',
        json={'title': 'Note', 'content': 'Photosynthesis note about sunlight energy.'},
        headers=auth_headers(token),
    )
    note_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'Photosynthesis?'},
        headers=auth_headers(token),
    )
    job = json.loads(response.data)['data']['job']
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    assert response.status_code == 200
    response = client.get(
        f'/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/queries/1', headers=auth_headers(token)
    )
    result = json.loads(response.data)['data']
    assert result['citations']
    assert any(c.get('source_id') == ready_source for c in result['citations'])


def test_query_default_scope_searches_all(client, app, auth_client, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'photosynthesis sunlight energy'},
        headers=auth_headers(token),
    )
    job = json.loads(response.data)['data']['job']
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    assert response.status_code == 200
    # Now ask a question that is not in the evidence; default scope is still used.
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'quantum entanglement'},
        headers=auth_headers(token),
    )
    job2 = json.loads(response.data)['data']['job']
    response = client.post(
        f'/api/v1/jobs/{job2["id"]}/run', headers=auth_headers(token)
    )
    body = json.loads(response.data)
    assert body['data']['status'] == GenerationJob.SUCCEEDED


def test_query_scope_isolation(client, app, auth_client, two_users, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']

    # Bob creates a workspace and a note.
    response = client.post('/api/auth/login', json={
        'username': 'bob', 'password': 'password123'
    })
    bob_token = json.loads(response.data)['data']['token']
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'Bob WS'},
        headers=auth_headers(bob_token),
    )
    bob_ws = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{bob_ws}/notes',
        json={'title': 'B', 'content': 'B content'},
        headers=auth_headers(bob_token),
    )
    bob_note = json.loads(response.data)['data']['id']

    # Alice tries to query her own workspace but pin Bob's note.
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': '?', 'note_ids': [bob_note]},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


def test_query_insufficient_evidence(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'anything'},
        headers=auth_headers(token),
    )
    job = json.loads(response.data)['data']['job']
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/queries/1', headers=auth_headers(token)
    )
    result = json.loads(response.data)['data']
    assert result['status'] == Query.SUCCEEDED
    assert 'not contain enough evidence' in result['answer'].lower()
    assert result['citations'] == []


def test_query_idempotent_rerun(client, app, auth_client, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/queries',
        json={'question': 'What is photosynthesis?'},
        headers=auth_headers(token),
    )
    payload = json.loads(response.data)['data']
    response = client.post(
        f'/api/v1/jobs/{payload["job"]["id"]}/run', headers=auth_headers(token)
    )
    first_body = json.loads(response.data)['data']
    assert first_body['status'] == GenerationJob.SUCCEEDED
    # Run a second time: still succeeded, no error.
    response = client.post(
        f'/api/v1/jobs/{payload["job"]["id"]}/run', headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert json.loads(response.data)['data']['status'] == GenerationJob.SUCCEEDED


def test_query_history_listed_newest_first(client, app, auth_client, ready_source):
    client, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces', headers=auth_headers(token)
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    for q in ('first', 'second', 'third'):
        client.post(
            f'/api/v1/workspaces/{ws_id}/queries',
            json={'question': q},
            headers=auth_headers(token),
        )
    response = client.get(
        f'/api/v1/workspaces/{ws_id}/queries', headers=auth_headers(token)
    )
    items = json.loads(response.data)['data']['items']
    assert [it['question'] for it in items] == ['third', 'second', 'first']
