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
    """Schema for login request validation."""
    email = fields.Email(required=True)
    password = fields.Str(required=True)

