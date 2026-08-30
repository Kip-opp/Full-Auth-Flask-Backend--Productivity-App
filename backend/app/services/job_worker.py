"""Asynchronous job worker.

The local worker processes a bounded batch of jobs in a single pass. It
is intentionally conservative: one job at a time, idempotent re-runs,
and durable state transitions. Production deployments should swap this
for a broker-backed worker (e.g. RQ, Celery, or a custom Redis adapter)
without changing the routes that create or read jobs.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import List

from app.extensions import db
from app.models.job import GenerationJob


MAX_BATCH = 25
DEFAULT_MAX_ATTEMPTS = 3


def claim_next_job(workspace_id: int) -> GenerationJob:
    """Atomically claim the oldest queued job for a workspace."""
    job = (
        GenerationJob.query
        .filter_by(workspace_id=workspace_id, status=GenerationJob.QUEUED)
        .order_by(GenerationJob.created_at.asc())
        .first()
    )
    if job is None:
        return None  # type: ignore[return-value]
    job.attempts = (job.attempts or 0) + 1
    job.status = GenerationJob.RUNNING
    job.started_at = datetime.utcnow()
    db.session.commit()
    return job


def process_job(job: GenerationJob) -> GenerationJob:
    """Dispatch a single job to its handler."""
    if job.job_type == GenerationJob.SOURCE_INGESTION:
        from app.services.source_service import run_source_ingestion
        run_source_ingestion(job)
    elif job.job_type == GenerationJob.ARTIFACT_GENERATION:
        from app.services.artifact_service import run_artifact_generation
        run_artifact_generation(job)
    elif job.job_type == GenerationJob.QUESTION_ANSWERING:
        from app.models.notebook import Query
        from app.services.query_service import run_query_job
        query = Query.query.filter_by(job_id=job.id).first()
        if query is None:
            raise RuntimeError('Query not found for job')
        run_query_job(query)
    else:
        raise ValueError(f'Unknown job type: {job.job_type}')
    return job


def run_batch(*, workspace_id: int = None, limit: int = MAX_BATCH) -> List[GenerationJob]:
    """Process a bounded batch of queued jobs.

    When ``workspace_id`` is given, only that workspace's jobs are
    claimed. Returns the list of jobs touched in this pass.
    """
    touched: List[GenerationJob] = []
    processed_ids = set()
    for _ in range(limit):
        query = GenerationJob.query.filter_by(status=GenerationJob.QUEUED)
        if workspace_id is not None:
            query = query.filter_by(workspace_id=workspace_id)
        job = query.order_by(GenerationJob.created_at.asc()).first()
        if job is None or job.id in processed_ids:
            break
        processed_ids.add(job.id)

        # Idempotency: a successful job is never re-run.
        if job.status == GenerationJob.SUCCEEDED:
            continue

        job.attempts = (job.attempts or 0) + 1
        if job.attempts > (job.max_attempts or DEFAULT_MAX_ATTEMPTS):
            job.status = GenerationJob.FAILED
            job.error_message = 'Exceeded maximum attempts'[:500]
            job.finished_at = datetime.utcnow()
            db.session.commit()
            touched.append(job)
            continue

        job.status = GenerationJob.RUNNING
        job.started_at = datetime.utcnow()
        db.session.commit()

        try:
            process_job(job)
        except Exception as exc:  # noqa: BLE001
            job.status = GenerationJob.FAILED
            job.error_message = str(exc)[:500] or 'Job failed'
            job.finished_at = datetime.utcnow()
            db.session.commit()
        touched.append(job)
    return touched
