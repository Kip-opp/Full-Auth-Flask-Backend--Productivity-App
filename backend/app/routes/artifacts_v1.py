"""Artifact CRUD + generation routes under ``/api/v1/workspaces/:id/artifacts``."""
import json
from flask import Blueprint, request
from marshmallow import ValidationError

from app.extensions import db
from app.models.artifact import Artifact, ArtifactSource
from app.models.job import GenerationJob
from app.models.source import Source
from app.schemas import ArtifactCreateSchema
from app.utils.decorators import token_required
from app.utils.responses import (
    success_response,
    error_response,
    validation_error_response,
)
from app.routes._helpers import get_owned_workspace


artifacts_bp = Blueprint('artifacts_v1', __name__,
                         url_prefix='/api/v1/workspaces/<int:workspace_id>/artifacts')


def _owned_artifact(workspace_id, artifact_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return None, error_response('NOT_FOUND', 'Artifact not found', 404)
    artifact = Artifact.query.filter_by(id=artifact_id, workspace_id=workspace.id).first()
    if artifact is None:
        return None, error_response('NOT_FOUND', 'Artifact not found', 404)
    return artifact, None


def _validated_sources(workspace_id, source_ids):
    """Confirm every supplied source belongs to the workspace."""
    if not source_ids:
        return []
    unique_ids = list({int(s) for s in source_ids if s})
    rows = (
        Source.query
        .filter(Source.id.in_(unique_ids), Source.workspace_id == workspace_id)
        .all()
    )
    found_ids = {row.id for row in rows}
    missing = [sid for sid in unique_ids if sid not in found_ids]
    if missing:
        return None, missing
    return rows, []


@artifacts_bp.route('', methods=['GET'])
@token_required
def list_artifacts(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)
    artifacts = (
        Artifact.query.filter_by(workspace_id=workspace.id)
        .order_by(Artifact.created_at.desc())
        .all()
    )
    return success_response(
        data={'items': [a.to_dict() for a in artifacts]},
        message='Artifacts retrieved successfully',
    )


@artifacts_bp.route('', methods=['POST'])
@token_required
def create_artifact(workspace_id):
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return error_response('NOT_FOUND', 'Workspace not found', 404)

    schema = ArtifactCreateSchema()
    try:
        data = schema.load(request.get_json() or {})
    except ValidationError as err:
        return validation_error_response(err.messages, 400)

    sources, missing = _validated_sources(workspace.id, data.get('source_ids') or [])
    if sources is None:
        return error_response(
            'INVALID_SOURCE_SCOPE',
            f'Sources not found in this workspace: {missing}',
            400,
        )

    artifact = Artifact(
        workspace_id=workspace.id,
        artifact_type=data['artifact_type'],
        title=data['title'],
        instructions=data.get('instructions', ''),
        status=Artifact.QUEUED,
        schema_version='1.0',
    )
    db.session.add(artifact)
    db.session.flush()

    for source in sources:
        db.session.add(ArtifactSource(artifact_id=artifact.id, source_id=source.id))

    job = GenerationJob(
        workspace_id=workspace.id,
        artifact_id=artifact.id,
        job_type=GenerationJob.ARTIFACT_GENERATION,
        status=GenerationJob.QUEUED,
        payload=json.dumps({'artifact_id': artifact.id}),
        max_attempts=3,
    )
    db.session.add(job)
    db.session.commit()

    return success_response(
        data={'artifact': artifact.to_dict(), 'job': job.to_dict()},
        message='Artifact queued for generation',
        status_code=201,
    )


@artifacts_bp.route('/<int:artifact_id>', methods=['GET'])
@token_required
def get_artifact(workspace_id, artifact_id):
    artifact, err = _owned_artifact(workspace_id, artifact_id)
    if err is not None:
        return err
    return success_response(data=artifact.to_dict(),
                            message='Artifact retrieved successfully')
