"""Shared pytest fixtures for the v1 test suites."""
import json
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db
from app.models.user import User
from app.models.workspace import Workspace


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def two_users(app):
    with app.app_context():
        alice = User(username='alice', email='alice@example.com')
        alice.set_password('password123')
        bob = User(username='bob', email='bob@example.com')
        bob.set_password('password123')
        db.session.add_all([alice, bob])
        db.session.commit()
        return {'alice_id': alice.id, 'bob_id': bob.id}


@pytest.fixture
def auth_client(client, app, two_users):
    """Return (client, token, user_id) for an authenticated alice.

    Reuses the alice created by :func:`two_users` so this fixture is
    composable with the cross-user ownership tests.
    """
    alice_id = two_users['alice_id']
    response = client.post('/api/auth/login', json={
        'username': 'alice',
        'password': 'password123',
    })
    token = json.loads(response.data)['data']['token']
    return client, token, alice_id


def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def workspace_for(client, app, auth_client):
    """Create a workspace for the authenticated user."""
    _, token, user_id = auth_client
    with app.app_context():
        ws = Workspace.query.filter_by(user_id=user_id).first()
        if ws is not None:
            return ws.id
    response = client.post(
        '/api/v1/workspaces',
        json={'name': 'Research', 'description': ''},
        headers=auth_headers(token),
    )
    return json.loads(response.data)['data']['id']


@pytest.fixture
def ready_source(workspace_for, app, auth_client):
    """Create a Source already in ``ready`` state with a Document and chunks."""
    from app.models.source import Source
    from app.models.document import Document, DocumentChunk
    with app.app_context():
        src = Source(
            workspace_id=workspace_for,
            url='https://example.com/article',
            title='Example Article',
            source_type='web',
            status=Source.READY,
            content_hash='abc123',
        )
        db.session.add(src)
        db.session.flush()
        doc = Document(
            source_id=src.id,
            canonical_url='https://example.com/article',
            title='Example Article',
            mime_type='text/html',
            text='Photosynthesis converts sunlight into chemical energy in plants.',
            word_count=9,
            version=1,
        )
        db.session.add(doc)
        db.session.flush()
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=0,
            text='Photosynthesis converts sunlight into chemical energy in plants.',
            token_count=9,
            locator='chars:0-67',
        )
        db.session.add(chunk)
        db.session.commit()
        return src.id
