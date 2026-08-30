"""Source management routes under ``/api/v1/workspaces/:id/sources``."""
import json
from datetime import datetime
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.source import Source
from app.models.job import GenerationJob
from app.schemas import SourceCreateSchema
from app.services.url_safety import URLValidationError, normalize_url, validate_public_url
from app.utils.decorators import token_required
from app.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
)
from app.routes._helpers import get_owned_workspace


sources_bp = Blueprint('sources_v1', __name__,
                       url_prefix='/api/v1/workspaces/<int:workspace_id>/sources')


def _owned_source(workspace_id, source_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return None, error_response('NOT_FOUND', 'Source not found', 404)
    source = Source.query.filter_by(id=source_id, workspace_id=workspace.id).first()
    if source is None:
        return None, error_response('NOT_FOUND', 'Source not found', 404)
    return source, None


@sources_bp.route('', methods=['GET'])
@token_required
def list_sources(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    sources = (
        Source.query.filter_by(workspace_id=workspace.id)
        .order_by(Source.created_at.desc())
        .all()
    )
    return success_response(
        data={'items': [s.to_dict() for s in sources]},
        message='Sources retrieved successfully',
    )


@sources_bp.route('', methods=['POST'])
@token_required
def queue_source(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)

    schema = SourceCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    try:
        safe_url = validate_public_url(data['url'])
    except URLValidationError as exc:
        return error_response('INVALID_URL', str(exc), 400)

    canonical = normalize_url(safe_url)

    existing = (
        Source.query.filter_by(workspace_id=workspace.id, url=canonical).first()
    )
    if existing is not None:
        return success_response(
            data={'source': existing.to_dict(), 'job': None, 'duplicate': True},
            message='Source already exists for this workspace',
            status_code=200,
        )

    if workspace.sources and len(workspace.sources) >= 100:
        return error_response('LIMIT_EXCEEDED', 'Source limit reached for workspace', 400)

    source = Source(
        workspace_id=workspace.id,
        url=canonical,
        title=(data.get('title') or '').strip()[:512],
        source_type='web',
        status=Source.QUEUED,
    )
    db.session.add(source)
    db.session.flush()

    job = GenerationJob(
        workspace_id=workspace.id,
        job_type=GenerationJob.SOURCE_INGESTION,
        status=GenerationJob.QUEUED,
        payload=json.dumps({'source_id': source.id}),
        max_attempts=3,
    )
    db.session.add(job)
    db.session.commit()

    return success_response(
        data={'source': source.to_dict(), 'job': job.to_dict()},
        message='Source queued for ingestion',
        status_code=201,
    )


@sources_bp.route('/<int:source_id>', methods=['GET'])
@token_required
def get_source(workspace_id, source_id):
    source, err = _owned_source(workspace_id, source_id)
    if err is not None:
        return err
    return success_response(data=source.to_dict(),
                            message='Source retrieved successfully')


@sources_bp.route('/<int:source_id>', methods=['DELETE'])
@token_required
def delete_source(workspace_id, source_id):
    source, err = _owned_source(workspace_id, source_id)
    if err is not None:
        return err
    db.session.delete(source)
    db.session.commit()
    return success_response(message='Source deleted successfully')


@sources_bp.route('/<int:source_id>/sync', methods=['POST'])
@token_required
def resync_source(workspace_id, source_id):
    source, err = _owned_source(workspace_id, source_id)
    if err is not None:
        return err

    source.status = Source.QUEUED
    source.error_message = ''
    source.last_synced_at = None

    job = GenerationJob(
        workspace_id=source.workspace_id,
        job_type=GenerationJob.SOURCE_INGESTION,
        status=GenerationJob.QUEUED,
        payload=json.dumps({'source_id': source.id}),
        max_attempts=3,
    )
    db.session.add(job)
    db.session.commit()

    return success_response(
        data={'source': source.to_dict(), 'job': job.to_dict()},
        message='Source queued for re-sync',
        status_code=202,
    )
