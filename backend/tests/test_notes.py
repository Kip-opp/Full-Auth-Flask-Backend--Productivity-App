"""Notes CRUD tests."""
import pytest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.note import Note
from app.config import TestingConfig


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def users(app):
    """Create demo users."""
    with app.app_context():
        alice = User(username='alice', email='alice@example.com')
        alice.set_password('password123')
        
        bob = User(username='bob', email='bob@example.com')
        bob.set_password('password123')
        
        db.session.add(alice)
        db.session.add(bob)
        db.session.commit()
        
        return {'alice': alice, 'bob': bob}


@pytest.fixture
def alice_token(client):
    """Get token for alice."""
    response = client.post('/api/auth/login', json={
        'username': 'alice',
        'password': 'password123'
    })
    return json.loads(response.data)['data']['token']


class TestCreateNote:
    """Test note creation."""

    def test_create_note_success(self, client, users, alice_token):
        """Test successful note creation."""
        response = client.post(
            '/api/notes',
            json={
                'title': 'Test Note',
                'content': 'This is a test note.',
                'status': 'active'
            },
            headers={'Authorization': f'Bearer {alice_token}'}
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True


class TestListNotes:
    """Test note listing with pagination."""

    def test_list_notes_empty(self, client, alice_token):
        """Test listing notes when none exist."""
        response = client.get(
            '/api/notes',
            headers={'Authorization': f'Bearer {alice_token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['items'] == []


class TestDeleteNote:
    """Test note deletion."""

    def test_delete_note_success(self, client, users, alice_token, app):
        """Test successful note deletion."""
        with app.app_context():
            note = Note(
                user_id=users['alice'].id,
                title='To Delete',
                content='Content'
            )
            db.session.add(note)
            db.session.commit()
            note_id = note.id

        response = client.delete(
            f'/api/notes/{note_id}',
            headers={'Authorization': f'Bearer {alice_token}'}
        )
        
        assert response.status_code == 200