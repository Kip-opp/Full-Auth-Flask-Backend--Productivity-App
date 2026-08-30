"""Job polling and local-only execution hook."""
from datetime import datetime
from flask import Blueprint, request

from app.extensions import db
from app.models.job import GenerationJob
from app.models.workspace import Workspace
from app.utils.decorators import token_required
from app.utils.responses import success_response, error_response
from app.services.job_worker import process_job


jobs_bp = Blueprint('jobs_v1', __name__, url_prefix='/api/v1/jobs')


def _owned_job(job_id):
    job = GenerationJob.query.get(job_id)
    if job is None:
        return None, error_response('NOT_FOUND', 'Job not found', 404)
    workspace = (
        Workspace.query
        .filter_by(id=job.workspace_id, user_id=request.user.id)
        .first()
    )
    if workspace is None:
        return None, error_response('NOT_FOUND', 'Job not found', 404)
    return job, None


@jobs_bp.route('/<int:job_id>', methods=['GET'])
@token_required
def get_job(job_id):
    job, err = _owned_job(job_id)
    if err is not None:
        return err
    return success_response(data=job.to_dict(),
                            message='Job retrieved successfully')


@jobs_bp.route('/<int:job_id>/run', methods=['POST'])
@token_required
def run_job(job_id):
    """Local-only execution hook.

    In production this endpoint should be disabled. It exists so the
    development client can advance a single job without a queue worker.
    """
    job, err = _owned_job(job_id)
    if err is not None:
        return err

    if job.status == GenerationJob.SUCCEEDED:
        return success_response(data=job.to_dict(),
                                message='Job already succeeded (idempotent no-op)')
    if job.status == GenerationJob.RUNNING:
        return success_response(data=job.to_dict(),
                                message='Job is already running')

    job.status = GenerationJob.RUNNING
    job.attempts = (job.attempts or 0) + 1
    job.started_at = datetime.utcnow()
    db.session.commit()

    try:
        process_job(job)
    except Exception as exc:  # noqa: BLE001
        job.status = GenerationJob.FAILED
        job.error_message = str(exc)[:500] or 'Job failed'
        job.finished_at = datetime.utcnow()
        db.session.commit()
        return success_response(data=job.to_dict(),
                                message='Job failed',
                                status_code=200)
    return success_response(data=job.to_dict(),
                            message='Job executed')
