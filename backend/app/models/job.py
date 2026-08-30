"""GenerationJob model: durable record of asynchronous work.

A GenerationJob is created whenever a request needs an external fetch or
model call. Workers transition jobs through ``queued`` -> ``running`` ->
``succeeded`` or ``failed``. Re-running a successful job is a no-op for
``artifact_generation``; ``source_ingestion`` re-runs only on a new content
hash and ``question_answering`` re-runs idempotently.
"""
from datetime import datetime
from app.extensions import db


class GenerationJob(db.Model):
    """A durable, auditable unit of asynchronous work."""
    __tablename__ = 'generation_jobs'

    SOURCE_INGESTION = 'source_ingestion'
    ARTIFACT_GENERATION = 'artifact_generation'
    QUESTION_ANSWERING = 'question_answering'
    JOB_TYPES = (SOURCE_INGESTION, ARTIFACT_GENERATION, QUESTION_ANSWERING)

    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    STATUSES = (QUEUED, RUNNING, SUCCEEDED, FAILED)

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    artifact_id = db.Column(db.Integer, db.ForeignKey('artifacts.id', ondelete='SET NULL'),
                            nullable=True, index=True)
    job_type = db.Column(db.String(40), nullable=False, index=True)
    status = db.Column(db.String(20), default=QUEUED, nullable=False, index=True)
    payload = db.Column(db.Text, default='{}', nullable=False)
    result = db.Column(db.Text, default='', nullable=False)
    attempts = db.Column(db.Integer, default=0, nullable=False)
    max_attempts = db.Column(db.Integer, default=3, nullable=False)
    error_message = db.Column(db.Text, default='', nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    qa_query = db.relationship('Query', backref='job', uselist=False,
                               foreign_keys='Query.job_id')

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'artifact_id': self.artifact_id,
            'job_type': self.job_type,
            'status': self.status,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'finished_at': self.finished_at.isoformat() if self.finished_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
