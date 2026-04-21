"""Note model for user-owned notes."""
from datetime import datetime
from app.extensions import db


class Note(db.Model):
    """Note model representing a user's note."""
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(
        db.String(20),
        default='active',
        nullable=False,
        index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def __repr__(self):
        return f'<Note {self.title}>'

    def to_dict(self):
        """Convert note to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    @staticmethod
    def belongs_to_user(note_id, user_id):
        """Check if note belongs to user (ownership enforcement)."""
        return Note.query.filter_by(id=note_id, user_id=user_id).first()


class TokenBlocklist(db.Model):
    """Token blocklist for logout token revocation."""
    __tablename__ = 'token_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.Text, nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<TokenBlocklist {self.id}>'

    @staticmethod
    def is_token_blocked(token):
        """Check if token is in blocklist (revoked)."""
        return TokenBlocklist.query.filter_by(token=token).first() is not None

    @staticmethod
    def add_to_blocklist(token, user_id, expires_at):
        """Add token to blocklist (revoke it)."""
        blocklist_entry = TokenBlocklist(
            token=token,
            user_id=user_id,
            expires_at=expires_at
        )
        db.session.add(blocklist_entry)
        db.session.commit()

    @staticmethod
    def cleanup_expired():
        """Remove expired tokens from blocklist."""
        TokenBlocklist.query.filter(
            TokenBlocklist.expires_at < datetime.utcnow()
        ).delete()
        db.session.commit()