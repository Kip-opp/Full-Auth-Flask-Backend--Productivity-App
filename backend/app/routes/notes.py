"""Notes CRUD routes with ownership enforcement and pagination."""
from flask import Blueprint, request, current_app
from marshmallow import ValidationError
from app.extensions import db
from app.models.note import Note
from app.schemas import NoteSchema, NoteCreateSchema, NoteUpdateSchema
from app.utils.responses import success_response, error_response, validation_error_response
from app.utils.decorators import token_required

notes_bp = Blueprint('notes', __name__, url_prefix='/api/notes')


@notes_bp.route('', methods=['POST'])
@token_required
def create_note():
    """Create new note for authenticated user."""
    schema = NoteCreateSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    try:
        note = Note(
            user_id=request.user.id,
            title=data['title'],
            content=data['content'],
            status=data.get('status', 'active')
        )
        
        db.session.add(note)
        db.session.commit()

        return success_response(
            data=note.to_dict(),
            message='Note created successfully',
            status_code=201
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            'CREATE_ERROR',
            'Failed to create note',
            500
        )


@notes_bp.route('', methods=['GET'])
@token_required
def list_notes():
    """List all notes for authenticated user with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', current_app.config['ITEMS_PER_PAGE'], type=int)
        status = request.args.get('status', None, type=str)

        if page < 1:
            page = 1
        if per_page < 1 or per_page > current_app.config['MAX_ITEMS_PER_PAGE']:
            per_page = current_app.config['ITEMS_PER_PAGE']

        query = Note.query.filter_by(user_id=request.user.id)
        
        if status:
            if status not in ['active', 'archived']:
                return error_response(
                    'INVALID_STATUS',
                    'Status must be active or archived',
                    400
                )
            query = query.filter_by(status=status)

        paginated = query.order_by(Note.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return success_response(
            data={
                'items': [note.to_dict() for note in paginated.items],
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'per_page': per_page,
            },
            message='Notes retrieved successfully',
            status_code=200
        )
    except Exception as e:
        return error_response(
            'LIST_ERROR',
            'Failed to retrieve notes',
            500
        )


@notes_bp.route('/<int:note_id>', methods=['GET'])
@token_required
def get_note(note_id):
    """Get single note by ID (ownership required)."""
    note = Note.belongs_to_user(note_id, request.user.id)
    
    if not note:
        return error_response(
            'NOT_FOUND',
            'Note not found',
            404
        )

    return success_response(
        data=note.to_dict(),
        message='Note retrieved successfully',
        status_code=200
    )


@notes_bp.route('/<int:note_id>', methods=['PATCH'])
@token_required
def update_note(note_id):
    """Update note by ID (ownership required)."""
    note = Note.belongs_to_user(note_id, request.user.id)
    
    if not note:
        return error_response(
            'NOT_FOUND',
            'Note not found',
            404
        )

    schema = NoteUpdateSchema()
    
    try:
        data = schema.load(request.get_json())
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    try:
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']
        if 'status' in data:
            note.status = data['status']

        db.session.commit()

        return success_response(
            data=note.to_dict(),
            message='Note updated successfully',
            status_code=200
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            'UPDATE_ERROR',
            'Failed to update note',
            500
        )


@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(note_id):
    """Delete note by ID (ownership required)."""
    note = Note.belongs_to_user(note_id, request.user.id)
    
    if not note:
        return error_response(
            'NOT_FOUND',
            'Note not found',
            404
        )

    try:
        db.session.delete(note)
        db.session.commit()

        return success_response(
            message='Note deleted successfully',
            status_code=200
        )
    except Exception as e:
        db.session.rollback()
        return error_response(
            'DELETE_ERROR',
            'Failed to delete note',
            500
        )