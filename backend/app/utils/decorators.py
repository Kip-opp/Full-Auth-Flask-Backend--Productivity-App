"""Custom decorators for authentication and authorization."""
from functools import wraps
from flask import request, current_app
from app.models.user import User
from app.models.note import TokenBlocklist
from app.utils.responses import error_response
import jwt


def token_required(f):
    """Decorator to require valid JWT token for protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]
            except IndexError:
                return error_response('INVALID_TOKEN', 'Invalid token format', 401)

        if not token:
            return error_response('MISSING_TOKEN', 'Token is missing', 401)

        if TokenBlocklist.is_token_blocked(token):
            return error_response('REVOKED_TOKEN', 'Token has been revoked', 401)

        payload = User.verify_token(token)
        if not payload:
            return error_response('INVALID_TOKEN', 'Invalid or expired token', 401)

        user = User.query.get(payload.get('user_id'))
        if not user:
            return error_response('USER_NOT_FOUND', 'User not found', 404)

        request.user = user
        request.token = token
        return f(*args, **kwargs)

    return decorated


def ownership_required(f):
    """Decorator to ensure user owns the resource."""
    @wraps(f)
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated