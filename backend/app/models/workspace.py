"""Workspace model: top-level tenant container owned by a user."""
from datetime import datetime
from app.extensions import db


class Workspace(db.Model):
    """Workspace owned by a single user.

    A workspace groups sources, notebook notes, queries, and generated
    artifacts. Every cross-resource relationship below is scoped to a
    workspace, which in turn is owned by exactly one user.
    """
    __tablename__ = 'workspaces'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default='', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    sources = db.relationship('Source', backref='workspace', lazy=True,
                             cascade='all, delete-orphan')
    artifacts = db.relationship('Artifact', backref='workspace', lazy=True,
                                cascade='all, delete-orphan')
    jobs = db.relationship('GenerationJob', backref='workspace', lazy=True,
                           cascade='all, delete-orphan')
    notebook_notes = db.relationship('WorkspaceNote', backref='workspace', lazy=True,
                                     cascade='all, delete-orphan')
    queries = db.relationship('Query', backref='workspace', lazy=True,
                              cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
