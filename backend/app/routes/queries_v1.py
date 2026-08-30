"""Notebook Q&A routes under ``/api/v1/workspaces/:id/queries``."""
import json
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.job import GenerationJob
from app.models.notebook import Query
from app.models.notebook import WorkspaceNote
from app.models.source import Source
from app.schemas import QueryCreateSchema
from app.utils.decorators import token_required
from app.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
)
from app.routes._helpers import get_owned_workspace


queries_bp = Blueprint('queries_v1', __name__,
                       url_prefix='/api/v1/workspaces/<int:workspace_id>/queries')


def _validate_scope(workspace_id, source_ids, note_ids):
    """Ensure every supplied source/note belongs to the workspace."""
    if source_ids:
        source_ids = list({int(s) for s in source_ids if s})
        if source_ids:
            found = (
                Source.query
                .filter(Source.id.in_(source_ids),
                        Source.workspace_id == workspace_id)
                .count()
            )
            if found != len(source_ids):
                return error_response(
                    'INVALID_SOURCE_SCOPE',
                    'One or more sources do not belong to this workspace',
                    400,
                )
    if note_ids:
        note_ids = list({int(n) for n in note_ids if n})
        if note_ids:
            found = (
                WorkspaceNote.query
                .filter(WorkspaceNote.id.in_(note_ids),
                        WorkspaceNote.workspace_id == workspace_id)
                .count()
            )
            if found != len(note_ids):
                return error_response(
                    'INVALID_NOTE_SCOPE',
                    'One or more notes do not belong to this workspace',
                    400,
                )
    return None


@queries_bp.route('', methods=['GET'])
@token_required
def list_queries(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    queries = (
        Query.query.filter_by(workspace_id=workspace.id)
        .order_by(Query.created_at.desc())
        .limit(50)
        .all()
    )
    return success_response(
        data={'items': [q.to_dict() for q in queries]},
        message='Queries retrieved successfully',
    )


@queries_bp.route('', methods=['POST'])
@token_required
def create_query(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    schema = QueryCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    source_ids = data.get('source_ids') or []
    note_ids = data.get('note_ids') or []
    err = _validate_scope(workspace.id, source_ids, note_ids)
    if err is not None:
        return err

    job = GenerationJob(
        workspace_id=workspace.id,
        job_type=GenerationJob.QUESTION_ANSWERING,
        status=GenerationJob.QUEUED,
        max_attempts=3,
    )
    db.session.add(job)
    db.session.flush()

    query = Query(
        workspace_id=workspace.id,
        job_id=job.id,
        question=data['question'],
        status=Query.QUEUED,
        source_ids=json.dumps(sorted({int(s) for s in source_ids})),
        note_ids=json.dumps(sorted({int(n) for n in note_ids})),
    )
    db.session.add(query)
    db.session.commit()

    return success_response(
        data={'query': query.to_dict(), 'job': job.to_dict()},
        message='Question queued',
        status_code=201,
    )


@queries_bp.route('/<int:query_id>', methods=['GET'])
@token_required
def get_query(workspace_id, query_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Query not found', 404)
    query = Query.query.filter_by(id=query_id, workspace_id=workspace.id).first()
    if query is None:
        return error_response('NOT_FOUND', 'Query not found', 404)
    payload = query.to_dict()
    if query.job_id is not None:
        job = GenerationJob.query.get(query.job_id)
        if job is not None and job.workspace_id == workspace.id:
            payload['job'] = job.to_dict()
    return success_response(data=payload,
                            message='Query retrieved successfully')
