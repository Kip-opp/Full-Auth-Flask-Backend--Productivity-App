"""Document and DocumentChunk models.

A Document is a single ingested snapshot of a Source. The same Source can
have multiple Documents over time (one per re-sync). Chunks are deterministic
units used by retrieval and generation.
"""
from datetime import datetime
from app.extensions import db


class Document(db.Model):
    """A normalized snapshot of a Source at a given point in time."""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('sources.id', ondelete='CASCADE'),
                          nullable=False, index=True)
    canonical_url = db.Column(db.String(2048), default='', nullable=False)
    title = db.Column(db.String(512), default='', nullable=False)
    mime_type = db.Column(db.String(120), default='text/plain', nullable=False)
    text = db.Column(db.Text, default='', nullable=False)
    word_count = db.Column(db.Integer, default=0, nullable=False)
    version = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    chunks = db.relationship('DocumentChunk', backref='document', lazy=True,
                             cascade='all, delete-orphan',
                             order_by='DocumentChunk.chunk_index.asc()')

    __table_args__ = (
        db.UniqueConstraint('source_id', 'version', name='uq_documents_source_version'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'canonical_url': self.canonical_url,
            'title': self.title,
            'mime_type': self.mime_type,
            'word_count': self.word_count,
            'version': self.version,
            'created_at': self.created_at.isoformat(),
        }


class DocumentChunk(db.Model):
    """A bounded slice of a Document used for retrieval."""
    __tablename__ = 'document_chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id', ondelete='CASCADE'),
                            nullable=False, index=True)
    chunk_index = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, default='', nullable=False)
    token_count = db.Column(db.Integer, default=0, nullable=False)
    locator = db.Column(db.String(255), default='', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_doc_index'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'token_count': self.token_count,
            'locator': self.locator,
        }
