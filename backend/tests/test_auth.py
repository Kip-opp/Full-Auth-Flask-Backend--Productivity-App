"""Authentication tests."""
import pytest
import json
from app import create_app
from app.extensions import db
from app.models.user import User
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
def demo_user(app):
    """Create demo user for testing."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('password123')
        db.session.add(user)
        db.session.commit()
        return user


class TestSignup:
    """Test user signup endpoint."""

    def test_signup_success(self, client):
        """Test successful user signup."""
        response = client.post('/api/auth/signup', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data['data']

    def test_signup_duplicate_username(self, client, demo_user):
        """Test signup with duplicate username."""
        response = client.post('/api/auth/signup', json={
            'username': 'testuser',
            'email': 'another@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 400


class TestLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, demo_user):
        """Test successful login."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'token' in data['data']

    def test_login_invalid_password(self, client, demo_user):
        """Test login with invalid password."""
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401


class TestLogout:
    """Test user logout endpoint."""

    def test_logout_success(self, client, demo_user):
        """Test successful logout."""
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = json.loads(login_response.data)['data']['token']

        response = client.post(
            '/api/auth/logout',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200


class TestMe:
    """Test me endpoint."""

    def test_me_success(self, client, demo_user):
        """Test getting current user."""
        login_response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'password123'
        })
        token = json.loads(login_response.data)['data']['token']

        response = client.get(
            '/api/auth/me',
            headers={'Authorization': f'Bearer {token}'}
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['username'] == 'testuser'


class TestGoogleOAuth:
    """Google sign-in is env-gated; verify the route is absent by default."""

    def test_google_config_hidden_when_unset(self, client):
        response = client.get('/api/auth/google/config')
        assert response.status_code == 404

    def test_google_login_rejected_when_unset(self, client):
        response = client.post('/api/auth/google', json={'id_token': 'x'})
        assert response.status_code == 404

    def test_google_config_exposed_when_configured(self, app, client):
        app.config['GOOGLE_CLIENT_ID'] = 'demo-client-id.apps.googleusercontent.com'
        response = client.get('/api/auth/google/config')
        assert response.status_code == 200
        data = json.loads(response.data)['data']
        assert data['enabled'] is True
        assert data['client_id'] == 'demo-client-id.apps.googleusercontent.com'

    def test_google_login_provisions_user(self, app, client, monkeypatch):
        from app.services import google_oauth
        from app.models.user import User

        app.config['GOOGLE_CLIENT_ID'] = 'demo-client-id.apps.googleusercontent.com'

        class _Identity:
            google_sub = 'sub-1'
            email = 'jane@example.com'
            email_verified = True
            name = 'Jane Doe'

        monkeypatch.setattr(google_oauth, 'verify',
                            lambda id_token, access_token: _Identity())

        response = client.post('/api/auth/google', json={'id_token': 'abc'})
        assert response.status_code == 200
        body = json.loads(response.data)
        assert 'token' in body['data']
        with app.app_context():
            user = User.query.filter_by(email='jane@example.com').first()
            assert user is not None
            assert user.username == 'jane'