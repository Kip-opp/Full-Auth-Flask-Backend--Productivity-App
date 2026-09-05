"""Authentication routes: signup, login, logout, me endpoint."""
from flask import Blueprint, current_app, request
from marshmallow import ValidationError
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.note import TokenBlocklist
from app.schemas import SignupSchema, LoginSchema
from app.utils.responses import success_response, error_response, validation_error_response
from app.utils.decorators import token_required
from app.services import google_oauth

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User signup endpoint."""
    schema = SignupSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    if User.query.filter_by(username=data['username']).first():
        return error_response(
            'DUPLICATE_USERNAME',
            'Username already exists',
            400
        )

    if User.query.filter_by(email=data['email']).first():
        return error_response(
            'DUPLICATE_EMAIL',
            'Email already exists',
            400
        )

    try:
        user = User(
            username=data['username'],
            email=data['email']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

        token = user.generate_token()

        return success_response(
            data={
                'user': user.to_dict(),
                'token': token,
            },
            message='User registered successfully',
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            'SIGNUP_ERROR',
            'Failed to create user',
            500
        )


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    schema = LoginSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    identifier = data.get('identifier') or data.get('username') or data.get('email')
    user = User.query.filter(
        (User.email == identifier) | (User.username == identifier)
    ).first()

    if not user or not user.check_password(data['password']):
        return error_response(
            'INVALID_CREDENTIALS',
            'Invalid email or password',
            401
        )

    token = user.generate_token()

    return success_response(
        data={
            'user': user.to_dict(),
            'token': token,
        },
        message='Login successful',
        status_code=200
    )


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout():
    """User logout endpoint."""
    try:
        expires_at = datetime.utcnow() + timedelta(hours=168)
        
        TokenBlocklist.add_to_blocklist(
            request.token,
            request.user.id,
            expires_at
        )

        return success_response(
            message='Logout successful',
            status_code=200
        )
    except Exception as e:
        return error_response(
            'LOGOUT_ERROR',
            'Failed to logout',
            500
        )


@auth_bp.route('/me', methods=['GET'])
@token_required
def me():
    """Get current authenticated user."""
    return success_response(
        data=request.user.to_dict(),
        message='User retrieved successfully',
        status_code=200
    )


@auth_bp.route('/google/config', methods=['GET'])
def google_config():
    """Tell the client whether Google sign-in is available.

    When ``GOOGLE_CLIENT_ID`` is not configured the endpoint returns a
    404 so the client can hide the "Continue with Google" affordance
    instead of rendering a broken button.
    """
    if not google_oauth.is_configured():
        return error_response('NOT_FOUND', 'Google sign-in is not configured', 404)
    return success_response(
        data={
            'enabled': True,
            'client_id': current_app.config.get('GOOGLE_CLIENT_ID'),
        },
        message='Google sign-in is configured',
    )


@auth_bp.route('/google', methods=['POST'])
def login_with_google():
    """Authenticate a user via a Google ``id_token`` or ``access_token``.

    New Google identities are auto-provisioned as users; existing
    identities are matched by email. The route is a 404 when
    ``GOOGLE_CLIENT_ID`` is not configured.
    """
    if not google_oauth.is_configured():
        return error_response('NOT_FOUND', 'Google sign-in is not configured', 404)

    body = request.get_json(silent=True) or {}
    id_token = body.get('id_token') or body.get('idToken')
    access_token = body.get('access_token') or body.get('accessToken')

    try:
        identity = google_oauth.verify(id_token, access_token)
    except ValueError as exc:
        return error_response('INVALID_GOOGLE_TOKEN', str(exc), 401)

    if identity is None:
        return error_response(
            'INVALID_GOOGLE_TOKEN',
            'A Google id_token or access_token is required',
            400,
        )

    email = identity.email
    user = User.query.filter(
        (User.email == email) | (User.username == email.split('@', 1)[0])
    ).first()

    if user is None:
        # Auto-provision a workspace member from the Google identity.
        # The username is derived from the email local-part with a
        # numeric suffix if a clash already exists.
        base_username = (email.split('@', 1)[0] or 'user')[:80]
        username = base_username
        suffix = 1
        while User.query.filter_by(username=username).first() is not None:
            suffix += 1
            username = f'{base_username}{suffix}'[:80]
        user = User(username=username, email=email)
        # Google-authenticated accounts have no password. The bcrypt
        # field is non-nullable, so store an unguessable random value.
        import secrets
        user.set_password(secrets.token_urlsafe(48))
        db.session.add(user)
        db.session.commit()

    token = user.generate_token()
    return success_response(
        data={'user': user.to_dict(), 'token': token},
        message='Google sign-in successful',
        status_code=200,
    )