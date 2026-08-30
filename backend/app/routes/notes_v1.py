"""Notebook notes routes under ``/api/v1/workspaces/:id/notes``."""
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.notebook import WorkspaceNote
from app.schemas import WorkspaceNoteCreateSchema, WorkspaceNoteUpdateSchema
from app.utils.decorators import token_required
from app.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
)
from app.routes._helpers import get_owned_workspace


notes_bp = Blueprint('workspace_notes_v1', __name__,
                     url_prefix='/api/v1/workspaces/<int:workspace_id>/notes')


def _owned_note(workspace_id, note_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return None, error_response('NOT_FOUND', 'Note not found', 404)
    note = WorkspaceNote.query.filter_by(id=note_id, workspace_id=workspace.id).first()
    if note is None:
        return None, error_response('NOT_FOUND', 'Note not found', 404)
    return note, None


@notes_bp.route('', methods=['GET'])
@token_required
def list_notes(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    include_archived = request.args.get('include_archived', 'false').lower() == 'true'
    query = WorkspaceNote.query.filter_by(workspace_id=workspace.id)
    if not include_archived:
        query = query.filter_by(status=WorkspaceNote.ACTIVE)
    notes = query.order_by(WorkspaceNote.updated_at.desc()).all()
    return success_response(
        data={'items': [n.to_dict() for n in notes]},
        message='Notes retrieved successfully',
    )


@notes_bp.route('', methods=['POST'])
@token_required
def create_note(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    schema = WorkspaceNoteCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)
    note = WorkspaceNote(
        workspace_id=workspace.id,
        title=data['title'],
        content=data.get('content', ''),
        status=data.get('status', 'active'),
    )
    db.session.add(note)
    db.session.commit()
    return success_response(data=note.to_dict(),
                            message='Note created successfully',
                            status_code=201)


@notes_bp.route('/<int:note_id>', methods=['PATCH'])
@token_required
def update_note(workspace_id, note_id):
    note, err = _owned_note(workspace_id, note_id)
    if err is not None:
        return err
    schema = WorkspaceNoteUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)
    if 'title' in data:
        note.title = data['title']
    if 'content' in data:
        note.content = data['content']
    if 'status' in data:
        note.status = data['status']
    db.session.commit()
    return success_response(data=note.to_dict(),
                            message='Note updated successfully')


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(workspace_id, note_id):
    note, err = _owned_note(workspace_id, note_id)
    if err is not None:
        return err
    db.session.delete(note)
    db.session.commit()
    return success_response(message='Note deleted successfully')
