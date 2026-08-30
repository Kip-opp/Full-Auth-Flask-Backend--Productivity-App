"""Routes package initialization."""
from app.routes.auth import auth_bp
from app.routes.notes import notes_bp
from app.routes.workspaces_v1 import workspaces_bp
from app.routes.sources_v1 import sources_bp
from app.routes.artifacts_v1 import artifacts_bp
from app.routes.jobs_v1 import jobs_bp
from app.routes.notes_v1 import notes_bp as workspace_notes_bp
from app.routes.queries_v1 import queries_bp

__all__ = [
    'auth_bp',
    'notes_bp',
    'workspaces_bp',
    'sources_bp',
    'artifacts_bp',
    'jobs_bp',
    'workspace_notes_bp',
    'queries_bp',
]
