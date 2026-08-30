"""Artifact and ArtifactSource models.

An Artifact is a generated deliverable (slides, mind map, table, quiz, or
summary) derived from a subset of a workspace's ready sources. The
ArtifactSource join table records which sources were used as evidence.
"""
from datetime import datetime
from app.extensions import db


class Artifact(db.Model):
    """Generated artifact belonging to a workspace."""
    __tablename__ = 'artifacts'

    QUEUED = 'queued'
    RUNNING = 'running'
    SUCCEEDED = 'succeeded'
    FAILED = 'failed'
    STATUSES = (QUEUED, RUNNING, SUCCEEDED, FAILED)

    ALLOWED_TYPES = ('slides', 'mindmap', 'table', 'quiz', 'summary')

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    artifact_type = db.Column(db.String(40), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default=QUEUED, nullable=False, index=True)
    instructions = db.Column(db.Text, default='', nullable=False)
    content = db.Column(db.Text, default='', nullable=False)
    error_message = db.Column(db.Text, default='', nullable=False)
    schema_version = db.Column(db.String(20), default='1.0', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    sources = db.relationship('ArtifactSource', backref='artifact', lazy=True,
                             cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'artifact_type': self.artifact_type,
            'title': self.title,
            'status': self.status,
            'instructions': self.instructions,
            'content': self.content,
            'error_message': self.error_message,
            'schema_version': self.schema_version,
            'sources': [link.source_id for link in self.sources],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class ArtifactSource(db.Model):
    """Join table: which sources were used to build an artifact."""
    __tablename__ = 'artifact_sources'

    artifact_id = db.Column(db.Integer, db.ForeignKey('artifacts.id', ondelete='CASCADE'),
                            primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id', ondelete='CASCADE'),
                          primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
