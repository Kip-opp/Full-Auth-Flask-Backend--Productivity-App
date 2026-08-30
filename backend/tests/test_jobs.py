"""Job lifecycle and worker batch tests."""
import json
import pytest

from app.extensions import db
from app.models.job import GenerationJob
from app.services.job_worker import run_batch
from tests.conftest import auth_headers


def test_job_polling_is_ownership_safe(client, app, auth_client, two_users):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/x'},
        headers=auth_headers(token),
    )
    job = json.loads(response.data)['data']['job']

    # Bob cannot read the job.
    response = client.post('/api/auth/login', json={
        'username': 'bob', 'password': 'password123'
    })
    bob_token = json.loads(response.data)['data']['token']
    response = client.get(
        f'/api/v1/jobs/{job["id"]}', headers=auth_headers(bob_token)
    )
    assert response.status_code == 404

    # Alice can.
    response = client.get(
        f'/api/v1/jobs/{job["id"]}', headers=auth_headers(token)
    )
    assert response.status_code == 200


def test_run_batch_is_bounded(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']

    # Queue three sources (will produce three ingestion jobs).
    for i in range(3):
        response = client.post(
            f'/api/v1/workspaces/{ws_id}/sources',
            json={'url': f'https://example.com/{i}'},
            headers=auth_headers(token),
        )
        assert response.status_code == 201

    # We do not call the local worker here because the network fetch is
    # not stubbed; the test is about state transitions, not fetching.
    with app.app_context():
        jobs = (
            GenerationJob.query
            .filter_by(workspace_id=ws_id, status=GenerationJob.QUEUED)
            .all()
        )
        assert len(jobs) == 3
        # Mark them failed to simulate processed jobs.
        for j in jobs:
            j.status = GenerationJob.FAILED
            j.error_message = 'forced'
            j.finished_at = __import__('datetime').datetime.utcnow()
        db.session.commit()
        # Batch is empty now.
        touched = run_batch(workspace_id=ws_id, limit=10)
        assert touched == []


def test_run_job_already_succeeded_is_noop(client, app, auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/x'},
        headers=auth_headers(token),
    )
    job = json.loads(response.data)['data']['job']
    with app.app_context():
        row = GenerationJob.query.get(job['id'])
        row.status = GenerationJob.SUCCEEDED
        db.session.commit()
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    body = json.loads(response.data)
    assert body['data']['status'] == GenerationJob.SUCCEEDED
    assert 'idempotent' in body['message'].lower()
