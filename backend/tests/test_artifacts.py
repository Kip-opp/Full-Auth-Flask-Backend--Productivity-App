"""Artifact route, provider, and job tests."""
import json
import pytest

from app.extensions import db
from app.models.artifact import Artifact, ArtifactSource
from app.models.job import GenerationJob
from app.models.source import Source
from app.services.artifact_providers import LocalArtifactProvider
from app.services.artifact_service import run_artifact_generation
from tests.conftest import auth_headers


@pytest.fixture
def workspace_with_source(client, app, auth_client, ready_source):
    _, token, _ = auth_client
    response = client.get(
        '/api/v1/workspaces',
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['items'][0]['id']
    return ws_id, ready_source


def test_artifact_type_allow_list(client, app, auth_client, workspace_with_source):
    client, token, _ = auth_client
    ws_id, src_id = workspace_with_source
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/artifacts',
        json={'artifact_type': 'unknown', 'title': 'X'},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


def test_artifact_creates_durable_job(client, app, auth_client, workspace_with_source):
    client, token, _ = auth_client
    ws_id, src_id = workspace_with_source
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/artifacts',
        json={
            'artifact_type': 'summary',
            'title': 'TL;DR',
            'instructions': '',
            'source_ids': [src_id],
        },
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    payload = json.loads(response.data)['data']
    assert payload['artifact']['status'] == Artifact.QUEUED
    assert payload['job']['job_type'] == GenerationJob.ARTIFACT_GENERATION
    assert payload['artifact']['sources'] == [src_id]


def test_artifact_run_idempotent(client, app, auth_client, workspace_with_source):
    client, token, _ = auth_client
    ws_id, src_id = workspace_with_source
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/artifacts',
        json={'artifact_type': 'mindmap', 'title': 'MM', 'source_ids': [src_id]},
        headers=auth_headers(token),
    )
    artifact = json.loads(response.data)['data']['artifact']
    job = json.loads(response.data)['data']['job']

    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    assert response.status_code == 200
    assert json.loads(response.data)['data']['status'] == GenerationJob.SUCCEEDED

    # Idempotent re-run: the artifact stays succeeded and the job stays succeeded.
    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    assert json.loads(response.data)['data']['status'] == GenerationJob.SUCCEEDED

    response = client.get(
        f'/api/v1/workspaces/{ws_id}/artifacts/{artifact["id"]}',
        headers=auth_headers(token),
    )
    body = json.loads(response.data)['data']
    assert body['status'] == Artifact.SUCCEEDED
    parsed = json.loads(body['content'])
    assert parsed['schema_version'] == '1.0'
    assert 'children' in parsed


def test_artifact_cross_workspace_rejected(client, app, auth_client, two_users,
                                            workspace_with_source):
    client, token, _ = auth_client
    ws_id, src_id = workspace_with_source
    # Bob (second user) tries to use Alice's source ID and workspace ID.
    response = client.post('/api/auth/login', json={
        'username': 'bob', 'password': 'password123'
    })
    bob_token = json.loads(response.data)['data']['token']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/artifacts',
        json={'artifact_type': 'slides', 'title': 'X', 'source_ids': [src_id]},
        headers=auth_headers(bob_token),
    )
    assert response.status_code == 404


def test_artifact_provider_shapes():
    provider = LocalArtifactProvider()
    evidence = [{
        'kind': 'source',
        'source_id': 1,
        'title': 'A',
        'locator': 'loc',
        'excerpt': 'A sentence.',
    }]
    for artifact_type, required in [
        ('slides', 'slides'),
        ('mindmap', 'children'),
        ('table', 'rows'),
        ('quiz', 'questions'),
        ('summary', 'summary'),
    ]:
        result = provider.generate(artifact_type, 't', 'i', evidence)
        assert result['schema_version'] == '1.0'
        assert required in result


def test_artifact_missing_source_ids_rejected(client, app, auth_client,
                                                workspace_with_source):
    client, token, _ = auth_client
    ws_id, _ = workspace_with_source
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/artifacts',
        json={'artifact_type': 'slides', 'title': 'X', 'source_ids': [9999]},
        headers=auth_headers(token),
    )
    assert response.status_code == 400
