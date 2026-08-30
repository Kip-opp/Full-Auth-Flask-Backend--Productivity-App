"""URL safety and SSRF guards for the local ingestion fetcher.

The MVP uses a built-in fetcher that runs in the same process. In production
this should be replaced with an egress proxy or a dedicated crawler service
that performs these checks out of band. The functions below are intentionally
strict: any loopback, private, link-local, or reserved network destination
is refused, regardless of how it is presented (host name or IP literal).
"""
from __future__ import annotations

import ipaddress
import socket
from typing import Optional
from urllib.parse import urlparse


ALLOWED_SCHEMES = ('http', 'https')
MAX_URL_LENGTH = 2048
MAX_FETCH_BYTES = 2 * 1024 * 1024  # 2 MiB
FETCH_TIMEOUT_SECONDS = 10


class URLValidationError(ValueError):
    """Raised when a URL fails the safety checks."""


def validate_public_url(url: str) -> str:
    """Validate the scheme, length, and host of an external URL.

    Returns the canonical scheme://netloc form. Raises
    :class:`URLValidationError` for any disallowed configuration.
    """
    if not url:
        raise URLValidationError('URL is required')
    if len(url) > MAX_URL_LENGTH:
        raise URLValidationError('URL is too long')

    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise URLValidationError('URL is malformed') from exc

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise URLValidationError('URL scheme must be http or https')
    if not parsed.hostname:
        raise URLValidationError('URL is missing a host')
    if parsed.username or parsed.password:
        raise URLValidationError('URL credentials are not allowed')

    host = parsed.hostname
    if host.lower() in {'localhost'}:
        raise URLValidationError('Local destinations are not allowed')

    try:
        # Resolve the host and refuse any private/loopback address.
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise URLValidationError('Could not resolve host') from exc

    for info in infos:
        sockaddr = info[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            continue
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise URLValidationError('Destination is not a public address')

    return f"{parsed.scheme.lower()}://{parsed.netloc}{parsed.path or ''}"


def is_private_host(host: str) -> bool:
    """Best-effort check used in tests and as a convenience helper."""
    try:
        validate_public_url(f'https://{host}/')
        return False
    except URLValidationError:
        return True


def normalize_url(url: str) -> str:
    """Return a stable, lower-cased canonical form for storage and dedup."""
    parsed = urlparse(url)
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{parsed.path or ''}"
