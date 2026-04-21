"""Routes package initialization."""
from app.routes.auth import auth_bp
from app.routes.notes import notes_bp

__all__ = ['auth_bp', 'notes_bp']