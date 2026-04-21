"""User model with authentication support."""
from datetime import datetime, timedelta
from app.extensions import db, bcrypt
import jwt
from flask import current_app


class User(db.Model):
    """User model representing an authenticated user."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    notes = db.relationship('Note', backref='author', lazy=True, cascade='all, delete-orphan')
    token_blocklist = db.relationship('TokenBlocklist', backref='user', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hash and store password using bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Verify plaintext password against stored hash."""
        return bcrypt.check_password_hash(self.password_hash, password)

    def generate_token(self):
        """Generate JWT token for authenticated user."""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'email': self.email,
            'exp': datetime.utcnow() + current_app.config['JWT_EXPIRATION_DELTA'],
        }
        token = jwt.encode(
            payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm='HS256'
        )
        return token

    @staticmethod
    def verify_token(token):
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )
            return payload
        except (jwt.InvalidTokenError, jwt.ExpiredSignatureError):
            return None

    def to_dict(self):
        """Convert user to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
