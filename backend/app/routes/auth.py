"""Authentication routes: signup, login, logout, me endpoint."""
from flask import Blueprint, request
from marshmallow import ValidationError
from datetime import datetime, timedelta
from app.extensions import db
from app.models.user import User
from app.models.note import TokenBlocklist
from app.schemas import SignupSchema, LoginSchema
from app.utils.responses import success_response, error_response, validation_error_response
from app.utils.decorators import token_required

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

    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return error_response(
            'INVALID_CREDENTIALS',
            'Invalid username or password',
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