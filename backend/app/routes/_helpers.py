"""HTTP route helpers for v1 endpoints."""
from flask import request
from app.models.workspace import Workspace
from app.utils.responses import error_response


def get_owned_workspace(workspace_id: int):
    """Return the workspace if the authenticated user owns it, else None.

    Cross-user IDs resolve to ``None`` so the caller can return a safe
    404. We never disclose whether the ID exists in another account.
    """
    user = getattr(request, 'user', None)
    if user is None:
        return None
    return Workspace.query.filter_by(id=workspace_id, user_id=user.id).first()


def workspace_or_404(workspace_id: int):
    """Return ``(workspace, error_response_or_None)``."""
    workspace = get_owned_workspace(workspace_id)
    if workspace is None:
        return None, error_response('NOT_FOUND', 'Workspace not found', 404)
    return workspace, None
