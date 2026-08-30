"""Source model: a URL ingested into a workspace.

A source starts in ``queued`` state, transitions to ``processing`` while the
ingestion service fetches and normalizes it, and ends in ``ready`` or
``failed``. The current version of a source is its latest Document; earlier
Document rows are retained for audit and retrieval evolution.
"""
from datetime import datetime
from app.extensions import db


class Source(db.Model):
    """A URL the user wants to use as evidence inside a workspace."""
    __tablename__ = 'sources'

    PENDING = 'pending'
    QUEUED = 'queued'
    PROCESSING = 'processing'
    READY = 'ready'
    FAILED = 'failed'
    STATUSES = (PENDING, QUEUED, PROCESSING, READY, FAILED)

    id = db.Column(db.Integer, primary_key=True)
    workspace_id = db.Column(db.Integer, db.ForeignKey('workspaces.id', ondelete='CASCADE'),
                             nullable=False, index=True)
    url = db.Column(db.String(2048), nullable=False)
    title = db.Column(db.String(512), default='', nullable=False)
    source_type = db.Column(db.String(40), default='web', nullable=False)
    status = db.Column(db.String(20), default=QUEUED, nullable=False, index=True)
    content_hash = db.Column(db.String(64), default='', nullable=False, index=True)
    error_message = db.Column(db.Text, default='', nullable=False)
    last_synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    documents = db.relationship('Document', backref='source', lazy=True,
                                cascade='all, delete-orphan',
                                order_by='Document.version.desc()')
    artifact_links = db.relationship('ArtifactSource', backref='source', lazy=True,
                                     cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'workspace_id': self.workspace_id,
            'url': self.url,
            'title': self.title,
            'source_type': self.source_type,
            'status': self.status,
            'content_hash': self.content_hash,
            'error_message': self.error_message,
            'last_synced_at': self.last_synced_at.isoformat() if self.last_synced_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
