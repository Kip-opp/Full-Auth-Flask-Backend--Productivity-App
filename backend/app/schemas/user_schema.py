"""User-related Marshmallow schemas."""
from marshmallow import Schema, fields, validate


class UserSchema(Schema):
    """Schema for user response serialization."""
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True, validate=validate.Length(min=3, max=80))
    email = fields.Email(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class SignupSchema(Schema):
    """Schema for signup request validation."""
    username = fields.Str(
        required=True,
        validate=validate.Length(min=3, max=80),
        error_messages={'required': 'Username is required'}
    )
    email = fields.Email(
        required=True,
        error_messages={'required': 'Email is required'}
    )
    password = fields.Str(
        required=True,
        validate=validate.Length(min=8),
        error_messages={'required': 'Password is required'}
    )



class LoginSchema(Schema):
    """Schema for login request validation.

    Accepts either ``username`` or ``email`` plus a password. This keeps the
    legacy ``/api/auth/login`` contract working with existing test fixtures
    while still allowing modern clients to authenticate with email.
    """
    username = fields.Str(load_default=None, validate=validate.Length(min=1, max=80))
    email = fields.Email(load_default=None)
    password = fields.Str(required=True)

    def validate_identifier(self, data, **_kwargs):
        if not data.get('username') and not data.get('email'):
            from marshmallow import ValidationError
            raise ValidationError('Either username or email is required')

