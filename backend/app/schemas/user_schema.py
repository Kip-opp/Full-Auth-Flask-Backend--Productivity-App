"""User-related Marshmallow schemas."""
from marshmallow import Schema, ValidationError, fields, validate, validates_schema


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

    ``identifier`` accepts either a username or an email address. The legacy
    fields remain accepted temporarily so older clients can migrate without
    an authentication outage.
    """
    identifier = fields.Str(load_default=None, validate=validate.Length(min=1, max=120))
    username = fields.Str(load_default=None, validate=validate.Length(min=1, max=80))
    email = fields.Email(load_default=None)
    password = fields.Str(required=True)

    @validates_schema
    def validate_identifier(self, data, **_kwargs):
        if not data.get('identifier') and not data.get('username') and not data.get('email'):
            raise ValidationError({'identifier': ['Identifier is required']})

