"""WorkspaceNote and Query models for the Ask-notebook experience.

``WorkspaceNote`` is the notebook writing primitive that lives inside a
workspace. ``Query`` records a user question along with the evidence scope
(ready sources + active notes), citations, and the durable GenerationJob
that produced the answer.
"""
from datetime import datetime
from app.extensions import db


class WorkspaceNote(db.Model):
    """A notebook note written inside one workspace."""
    __tablename__ = 'workspace_notes'

    ACTIVE = 'active'
    ARCHIVED = 'archived'
    STATUSES = (ACTIVE, ARCHIVED)

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, default='', nullable=False)
    status = db.Column(db.String(20), default=ACTIVE, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'title': self.title,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Query(db.Model):
    """A user question plus the grounded answer and citations."""
    __tablename__ = 'queries'

    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    STATUSES = (QUEUED, RUNNING, SUCCEEDED, FAILED)

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey('generation_jobs.id', ondelete='SET NULL'),
                       nullable=True, unique=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, default='', nullable=False)
    status = db.Column(db.String(20), default=QUEUED, nullable=False, index=True)
    citations = db.Column(db.Text, default='[]', nullable=False)
    source_ids = db.Column(db.Text, default='[]', nullable=False)
    note_ids = db.Column(db.Text, default='[]', nullable=False)
    error_message = db.Column(db.Text, default='', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    def to_dict(self):
        import json
        try:
            citations_list = json.loads(self.citations or '[]')
        except (TypeError, ValueError):
            citations_list = []
        try:
            sources_list = json.loads(self.source_ids or '[]')
        except (TypeError, ValueError):
            sources_list = []
        try:
            notes_list = json.loads(self.note_ids or '[]')
        except (TypeError, ValueError):
            notes_list = []
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'job_id': self.job_id,
            'question': self.question,
            'answer': self.answer,
            'status': self.status,
            'citations': citations_list,
            'source_ids': sources_list,
            'note_ids': notes_list,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
