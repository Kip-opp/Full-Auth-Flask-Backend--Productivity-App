"""Workspace CRUD routes under ``/api/v1/workspaces``."""
import json
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.workspace import Workspace
from app.schemas import WorkspaceCreateSchema, WorkspaceUpdateSchema
from app.utils.decorators import token_required
from app.utils.responses import success_response, error_response, validation_error_response
from app.routes._helpers import get_owned_workspace


workspaces_bp = Blueprint('workspaces_v1', __name__, url_prefix='/api/v1/workspaces')


@workspaces_bp.route('', methods=['GET'])
@token_required
def list_workspaces():
    workspaces = (
        Workspace.query
        .filter_by(user_id=request.user.id)
        .order_by(Workspace.created_at.desc())
        .all()
    )
    return success_response(
        data={'items': [w.to_dict() for w in workspaces]},
        message='Workspaces retrieved successfully',
    )


@workspaces_bp.route('', methods=['POST'])
@token_required
def create_workspace():
    schema = WorkspaceCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    workspace = Workspace(
        user_id=request.user.id,
        name=data['name'],
        description=data.get('description', ''),
    )
    db.session.add(workspace)
    db.session.commit()
    return success_response(
        data=workspace.to_dict(),
        message='Workspace created successfully',
        status_code=201,
    )


@workspaces_bp.route('/<int:workspace_id>', methods=['GET'])
@token_required
def get_workspace(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    return success_response(data=workspace.to_dict(),
                            message='Workspace retrieved successfully')


@workspaces_bp.route('/<int:workspace_id>', methods=['PATCH'])
@token_required
def update_workspace(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    schema = WorkspaceUpdateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)
    if 'name' in data:
        workspace.name = data['name']
    if 'description' in data:
        workspace.description = data['description']
    db.session.commit()
    return success_response(data=workspace.to_dict(),
                            message='Workspace updated successfully')


@workspaces_bp.route('/<int:workspace_id>', methods=['DELETE'])
@token_required
def delete_workspace(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    db.session.delete(workspace)
    db.session.commit()
    return success_response(message='Workspace deleted successfully')
