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