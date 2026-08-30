"""Source route and ingestion service tests."""
import json
import pytest

from app.extensions import db
from app.models.document import Document, DocumentChunk
from app.models.job import GenerationJob
from app.models.source import Source
from app.services.source_service import (
    chunk_text,
    fetch_and_normalize,
    normalize_html,
    run_source_ingestion,
)
from app.services.url_safety import URLValidationError, validate_public_url
from tests.conftest import auth_headers


def test_private_url_rejected():
    for url in [
        'http://127.0.0.1/x',
        'http://localhost/x',
        'http://10.0.0.5/x',
        'http://192.168.0.1/x',
        'http://169.254.169.254/latest/meta-data/',  # AWS metadata
        'ftp://example.com/x',
        'file:///etc/passwd',
        'http://user:pass@example.com/x',
    ]:
        with pytest.raises(URLValidationError):
            validate_public_url(url)


def test_https_url_accepted():
    url = validate_public_url('HTTPS://Example.com/Path')
    assert url.startswith('https://')


def test_source_validation_and_queue(auth_client):
    client, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']

    # Reject private URL
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'http://localhost/x'},
        headers=auth_headers(token),
    )
    assert response.status_code == 400

    # Reject missing scheme
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'not-a-url'},
        headers=auth_headers(token),
    )
    assert response.status_code == 400

    # Queue a public URL
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/post', 'title': 'Post'},
        headers=auth_headers(token),
    )
    assert response.status_code == 201
    payload = json.loads(response.data)['data']
    assert payload['source']['status'] == Source.QUEUED
    assert payload['job']['job_type'] == GenerationJob.SOURCE_INGESTION

    # Duplicate detection
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/post'},
        headers=auth_headers(token),
    )
    assert response.status_code == 200
    assert json.loads(response.data)['data']['duplicate'] is True


def test_source_ingestion_creates_document(client, app, auth_client, monkeypatch):
    _, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/page'},
        headers=auth_headers(token),
    )
    src = json.loads(response.data)['data']['source']
    job = json.loads(response.data)['data']['job']

    def fake_fetch(url):
        return (
            b'<html><head><title>Hi</title></head>'
            b'<body><p>Hello world this is a test of ingestion.</p></body></html>',
            'https://example.com/page',
            'text/html; charset=utf-8',
        )

    response = client.post(
        f'/api/v1/jobs/{job["id"]}/run', headers=auth_headers(token)
    )
    assert response.status_code == 200

    # Use the service directly with the stub to keep this test deterministic
    # without depending on the in-process network.
    with app.app_context():
        job_row = GenerationJob.query.get(job['id'])
        job_row.status = GenerationJob.QUEUED
        job_row.attempts = 0
        db.session.commit()
        run_source_ingestion(job_row, fetcher=fake_fetch)
        source = Source.query.get(src['id'])
        assert source.status == Source.READY
        assert source.content_hash != ''
        assert source.documents
        assert source.documents[0].chunks
        assert source.documents[0].chunks[0].chunk_index == 0


def test_failed_source_does_not_become_silent(client, app, auth_client):
    _, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'http://localhost/x'},
        headers=auth_headers(token),
    )
    assert response.status_code == 400


def test_ingestion_idempotent_same_hash(client, app, auth_client):
    _, token, _ = auth_client
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'WS'},
        headers=auth_headers(token),
    )
    ws_id = json.loads(response.data)['data']['id']
    response = client.post(
        f'/api/v1/workspaces/{ws_id}/sources',
        json={'url': 'https://example.com/page'},
        headers=auth_headers(token),
    )
    src = json.loads(response.data)['data']['source']
    job = json.loads(response.data)['data']['job']

    def fake_fetch(url):
        return (
            b'<html><body><p>Stable content for hashing tests.</p></body></html>',
            'https://example.com/page',
            'text/html',
        )

    with app.app_context():
        job_row = GenerationJob.query.get(job['id'])
        run_source_ingestion(job_row, fetcher=fake_fetch)
        first_version = Source.query.get(src['id']).documents[0].version
        first_hash = Source.query.get(src['id']).content_hash
        # Re-run with the same content
        job_row2 = GenerationJob(
            workspace_id=ws_id,
            job_type=GenerationJob.SOURCE_INGESTION,
            status=GenerationJob.QUEUED,
            payload=json.dumps({'source_id': src['id']}),
        )
        db.session.add(job_row2)
        db.session.commit()
        run_source_ingestion(job_row2, fetcher=fake_fetch)
        source = Source.query.get(src['id'])
        # Same content hash -> no new document version
        assert source.content_hash == first_hash
        assert len(source.documents) == 1
        assert source.documents[0].version == first_version


def test_chunking_deterministic():
    text = ' '.join(f'word{i}' for i in range(2000))
    first = chunk_text(text)
    second = chunk_text(text)
    assert first == second
    assert len(first) > 1
    for idx, (_, locator) in enumerate(first):
        assert locator.startswith('chars:')


def test_normalize_html_strips_scripts():
    text = normalize_html(
        '<html><head><script>alert(1)</script></head>'
        '<body><p>Hello <b>world</b></p></body></html>'
    )
    assert 'alert' not in text
    assert 'Hello world' in text


def test_fetch_and_normalize_byte_cap(app, monkeypatch):
    from app.services import source_service
    def fake_get(url, max_bytes=2 * 1024 * 1024, timeout=10):
        return (b'x' * (max_bytes + 10), url, 'text/html')
    monkeypatch.setattr(source_service, 'http_get', fake_get)
    with pytest.raises(URLValidationError):
        with app.app_context():
            fetch_and_normalize('https://example.com/big')
