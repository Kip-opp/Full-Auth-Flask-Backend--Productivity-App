"""Note-related Marshmallow schemas."""
from marshmallow import Schema, fields, validate


class NoteSchema(Schema):
    """Schema for note response serialization."""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    title = fields.Str()
    content = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class NoteCreateSchema(Schema):
    """Schema for note creation request validation."""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=255),
        error_messages={'required': 'Title is required'}
    )
    content = fields.Str(
        required=True,
        validate=validate.Length(min=1),
        error_messages={'required': 'Content is required'}
    )
    status = fields.Str(
        missing='active',
        validate=validate.OneOf(['active', 'archived'])
    )

    class Meta:
        strict = True


class NoteUpdateSchema(Schema):
    """Schema for note update request validation."""
    title = fields.Str(
        validate=validate.Length(min=1, max=255)
    )
    content = fields.Str(
        validate=validate.Length(min=1)
    )
    status = fields.Str(
        validate=validate.OneOf(['active', 'archived'])
    )

    class Meta:
        strict = True