"""Validation schemas for the v1 workspace API."""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


WORKSPACE_NAME_MAX = 120
WORKSPACE_DESC_MAX = 2000
SOURCE_URL_MAX = 2048
SOURCE_TITLE_MAX = 512
INSTRUCTION_MAX = 2000
TITLE_MAX = 255
CONTENT_MAX = 50_000
QUESTION_MAX = 2000
NOTE_TITLE_MAX = 255
NOTE_CONTENT_MAX = 50_000


def _positive_int_ids(value):
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValidationError('Expected a list of integer ids')
    cleaned = []
    for v in value:
        try:
            i = int(v)
        except (TypeError, ValueError):
            raise ValidationError('Each id must be an integer')
        if i <= 0:
            raise ValidationError('Ids must be positive')
        cleaned.append(i)
    return cleaned


class WorkspaceCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=WORKSPACE_NAME_MAX))
    description = fields.Str(load_default='', validate=validate.Length(max=WORKSPACE_DESC_MAX))


class WorkspaceUpdateSchema(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=WORKSPACE_NAME_MAX))
    description = fields.Str(validate=validate.Length(max=WORKSPACE_DESC_MAX))


class SourceCreateSchema(Schema):
    url = fields.Str(required=True, validate=validate.Length(min=1, max=SOURCE_URL_MAX))
    title = fields.Str(load_default='', validate=validate.Length(max=SOURCE_TITLE_MAX))


class ArtifactCreateSchema(Schema):
    artifact_type = fields.Str(
        required=True,
        validate=validate.OneOf(['slides', 'mindmap', 'table', 'quiz', 'summary']),
    )
    title = fields.Str(required=True, validate=validate.Length(min=1, max=TITLE_MAX))
    instructions = fields.Str(load_default='', validate=validate.Length(max=INSTRUCTION_MAX))
    source_ids = fields.List(fields.Int(), load_default=list)

    @validates_schema
    def _limit_sources(self, data, **_kwargs):
        ids = data.get('source_ids') or []
        if len(ids) > 50:
            raise ValidationError({'source_ids': ['Too many sources selected']})


class WorkspaceNoteCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=NOTE_TITLE_MAX))
    content = fields.Str(load_default='', validate=validate.Length(max=NOTE_CONTENT_MAX))
    status = fields.Str(load_default='active',
                        validate=validate.OneOf(['active', 'archived']))


class WorkspaceNoteUpdateSchema(Schema):
    title = fields.Str(validate=validate.Length(min=1, max=NOTE_TITLE_MAX))
    content = fields.Str(validate=validate.Length(max=NOTE_CONTENT_MAX))
    status = fields.Str(validate=validate.OneOf(['active', 'archived']))


class QueryCreateSchema(Schema):
    question = fields.Str(required=True, validate=validate.Length(min=1, max=QUESTION_MAX))
    source_ids = fields.List(fields.Int(), load_default=list)
    note_ids = fields.List(fields.Int(), load_default=list)

    @validates_schema
    def _limit_scope(self, data, **_kwargs):
        if len(data.get('source_ids') or []) > 50:
            raise ValidationError({'source_ids': ['Too many sources']})
        if len(data.get('note_ids') or []) > 50:
            raise ValidationError({'note_ids': ['Too many notes']})
