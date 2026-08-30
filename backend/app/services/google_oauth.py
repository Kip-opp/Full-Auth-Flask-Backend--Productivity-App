"""Google OAuth verification helpers.

The service is intentionally small: it accepts either an ``id_token`` or
an ``access_token`` and validates the resulting identity against Google
without taking a hard dependency on a third-party library. When
``GOOGLE_CLIENT_ID`` is not configured, the helpers return ``None`` and
the routes expose a 404 so the UI hides the Google button.

No credentials are written to source. Production deployments must
provide ``GOOGLE_CLIENT_ID`` (and optionally
``GOOGLE_ALLOWED_EMAILS``) via environment variables.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from flask import current_app


logger = logging.getLogger(__name__)


class GoogleIdentity:
    """The minimum identity the application needs from Google."""

    __slots__ = ('google_sub', 'email', 'email_verified', 'name')

    def __init__(self, google_sub, email, email_verified, name):
        self.google_sub = google_sub
        self.email = email
        self.email_verified = bool(email_verified)
        self.name = name or ''

    def to_dict(self):
        return {
            'sub': self.google_sub,
            'email': self.email,
            'email_verified': self.email_verified,
            'name': self.name,
        }


def is_configured() -> bool:
    """Return True if Google credentials have been provided."""
    return bool(current_app.config.get('GOOGLE_CLIENT_ID'))


def _http_get_json(url: str, *, timeout: float = 6.0) -> dict:
    req = urllib.request.Request(url, headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310
        body = response.read()
    try:
        return json.loads(body.decode('utf-8'))
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError('Invalid JSON from Google') from exc


def verify_id_token(id_token: str) -> Optional[GoogleIdentity]:
    """Validate a Google ``id_token`` and return the identity.

    Uses the public ``tokeninfo`` endpoint; the request itself is
    unauthenticated and Google checks the signature. The configured
    ``GOOGLE_CLIENT_ID`` must match the ``aud`` claim.
    """
    if not is_configured():
        return None
    if not id_token:
        raise ValueError('id_token is required')

    url = 'https://oauth2.googleapis.com/tokeninfo?' + urllib.parse.urlencode(
        {'id_token': id_token}
    )
    payload = _http_get_json(url)

    expected_audience = current_app.config.get('GOOGLE_CLIENT_ID')
    if expected_audience and payload.get('aud') != expected_audience:
        raise ValueError('Google audience mismatch')

    email = (payload.get('email') or '').strip().lower()
    if not email:
        raise ValueError('Google account has no email')
    if payload.get('email_verified') not in ('true', True, '1', 1):
        raise ValueError('Google email is not verified')

    allowed = current_app.config.get('GOOGLE_ALLOWED_EMAILS')
    if allowed and email not in allowed:
        raise ValueError('Google account is not allowed for this deployment')

    return GoogleIdentity(
        google_sub=payload.get('sub') or payload.get('user_id') or '',
        email=email,
        email_verified=True,
        name=(payload.get('name') or '').strip(),
    )


def verify_access_token(access_token: str) -> Optional[GoogleIdentity]:
    """Validate a Google OAuth ``access_token`` via userinfo."""
    if not is_configured():
        return None
    if not access_token:
        raise ValueError('access_token is required')

    url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    req = urllib.request.Request(url, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=6.0) as response:  # noqa: S310
            payload = json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        if exc.code in (401, 403):
            raise ValueError('Google access token was rejected') from exc
        raise

    email = (payload.get('email') or '').strip().lower()
    if not email or not payload.get('email_verified'):
        raise ValueError('Google account email is not verified')

    return GoogleIdentity(
        google_sub=payload.get('sub') or '',
        email=email,
        email_verified=True,
        name=(payload.get('name') or '').strip(),
    )


def verify(id_token: Optional[str], access_token: Optional[str]
           ) -> Optional[GoogleIdentity]:
    """Try ``id_token`` first, then ``access_token``."""
    if id_token:
        return verify_id_token(id_token)
    if access_token:
        return verify_access_token(access_token)
    return None
