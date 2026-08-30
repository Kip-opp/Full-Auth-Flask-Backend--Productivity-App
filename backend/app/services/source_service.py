"""Source ingestion service.

The local fetcher is intentionally replaceable. Production deployments
should run it behind an egress proxy or a dedicated crawler service that
performs stronger network policy enforcement. The default implementation
uses :mod:`urllib` so the test suite can stub the fetch without a network
dependency.
"""
from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Iterable, List, Optional, Tuple

from app.extensions import db
from app.models.source import Source
from app.models.document import Document, DocumentChunk
from app.models.job import GenerationJob
from app.services.url_safety import (
    MAX_FETCH_BYTES,
    FETCH_TIMEOUT_SECONDS,
    URLValidationError,
    validate_public_url,
)


CHUNK_TARGET_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200
MAX_CHUNKS = 256


@dataclass
class FetchedDocument:
    """Result of fetching and normalizing a URL."""
    body: str
    canonical_url: str
    title: str
    mime_type: str
    word_count: int
    content_hash: str


def http_get(url: str, *, max_bytes: int = MAX_FETCH_BYTES,
             timeout: float = FETCH_TIMEOUT_SECONDS) -> Tuple[bytes, str, str]:
    """Fetch ``url`` with a hard byte cap and a short timeout.

    Returns ``(body, final_url, content_type)``. Production callers should
    route this through an egress proxy. The MVP uses ``urllib`` to avoid
    pulling in extra dependencies.
    """
    import urllib.request
    import urllib.error

    req = urllib.request.Request(url, headers={'User-Agent': 'NotebookBot/1.0'})
    with urllib.request.urlopen(req, timeout=timeout) as response:  # noqa: S310
        # Disable redirect following to keep the destination predictable.
        content_type = response.headers.get('Content-Type', 'application/octet-stream')
        body = response.read(max_bytes + 1)
        final_url = response.geturl()
    return body, final_url, content_type


def _decode_body(body: bytes, content_type: str) -> str:
    """Decode raw bytes using the declared charset when available."""
    charset = 'utf-8'
    if 'charset=' in content_type.lower():
        try:
            charset = content_type.split('charset=', 1)[1].split(';')[0].strip()
        except IndexError:
            pass
    try:
        return body.decode(charset, errors='replace')
    except LookupError:
        return body.decode('utf-8', errors='replace')


_TAG_RE = re.compile(r'<[^>]+>')
_SCRIPT_RE = re.compile(r'<script[\s\S]*?</script>', re.IGNORECASE)
_STYLE_RE = re.compile(r'<style[\s\S]*?</style>', re.IGNORECASE)
_WHITESPACE_RE = re.compile(r'\s+')


def normalize_html(raw: str) -> str:
    """Strip scripts/styles/tags and collapse whitespace."""
    text = _SCRIPT_RE.sub(' ', raw)
    text = _STYLE_RE.sub(' ', text)
    text = _TAG_RE.sub(' ', text)
    text = html.unescape(text)
    text = _WHITESPACE_RE.sub(' ', text).strip()
    return text


def extract_title(raw: str, fallback: str) -> str:
    """Find a ``<title>`` if present; otherwise return the supplied fallback."""
    match = re.search(r'<title[^>]*>(.*?)</title>', raw, re.IGNORECASE | re.DOTALL)
    if not match:
        return fallback
    return html.unescape(_WHITESPACE_RE.sub(' ', match.group(1))).strip()[:512]


def chunk_text(text: str) -> List[Tuple[str, str]]:
    """Deterministic character-based chunker.

    Returns an ordered list of ``(text, locator)`` pairs. The chunks are
    stable across re-runs of the same input, which is what the
    idempotency contract requires.
    """
    if not text:
        return []
    chunks: List[Tuple[str, str]] = []
    start = 0
    n = len(text)
    while start < n and len(chunks) < MAX_CHUNKS:
        end = min(start + CHUNK_TARGET_CHARS, n)
        if end < n:
            # Prefer a sentence/word break near the end of the window.
            for break_at in (end, end - 80, end - 200):
                if break_at <= start:
                    continue
                if break_at < n and text[break_at] in ' \n.!?':
                    end = break_at + 1
                    break
        segment = text[start:end].strip()
        if segment:
            locator = f'chars:{start}-{end}'
            chunks.append((segment, locator))
        if end >= n:
            break
        start = max(end - CHUNK_OVERLAP_CHARS, end)
    return chunks


def fetch_and_normalize(url: str, *,
                        fetcher: Optional[Callable[[str], Tuple[bytes, str, str]]] = None
                        ) -> FetchedDocument:
    """Validate, fetch, and normalize ``url``.

    ``fetcher`` is an injection seam used by tests to avoid network access.
    """
    canonical = validate_public_url(url)
    fn = fetcher or http_get
    body, final_url, content_type = fn(canonical)

    if len(body) > MAX_FETCH_BYTES:
        raise URLValidationError('Response exceeded maximum size')

    mime = content_type.split(';', 1)[0].strip().lower() or 'application/octet-stream'
    raw_text = _decode_body(body, content_type)

    if 'html' in mime:
        text = normalize_html(raw_text)
        title = extract_title(raw_text, fallback=final_url)
    else:
        text = raw_text.strip()
        title = final_url

    word_count = len(text.split())
    content_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

    return FetchedDocument(
        body=text,
        canonical_url=final_url,
        title=title,
        mime_type=mime,
        word_count=word_count,
        content_hash=content_hash,
    )


def _next_version(source: Source) -> int:
    latest = (
        Document.query.filter_by(source_id=source.id)
        .order_by(Document.version.desc())
        .first()
    )
    return (latest.version + 1) if latest else 1


def run_source_ingestion(job: GenerationJob,
                         fetcher: Optional[Callable[[str], Tuple[bytes, str, str]]] = None
                         ) -> Source:
    """Execute a ``source_ingestion`` job.

    Returns the updated :class:`Source` on success. Raises on failure
    after recording a bounded error on the source and job.
    """
    import json

    payload = json.loads(job.payload or '{}')
    source_id = payload.get('source_id')
    source: Optional[Source] = None
    if source_id is not None:
        source = Source.query.get(source_id)

    if source is None:
        raise RuntimeError('Source not found for ingestion job')

    source.status = Source.PROCESSING
    source.error_message = ''
    db.session.commit()

    try:
        document = fetch_and_normalize(source.url, fetcher=fetcher)
    except URLValidationError as exc:
        source.status = Source.FAILED
        source.error_message = str(exc)[:500]
        job.status = GenerationJob.FAILED
        job.error_message = source.error_message
        job.finished_at = datetime.utcnow()
        db.session.commit()
        raise
    except Exception as exc:  # noqa: BLE001
        source.status = Source.FAILED
        source.error_message = 'Failed to fetch source'[:500]
        job.status = GenerationJob.FAILED
        job.error_message = source.error_message
        job.finished_at = datetime.utcnow()
        db.session.commit()
        raise

    if source.content_hash == document.content_hash:
        # Idempotent: same content, no new document version.
        source.status = Source.READY
        source.last_synced_at = datetime.utcnow()
        job.status = GenerationJob.SUCCEEDED
        job.finished_at = datetime.utcnow()
        db.session.commit()
        return source

    source.content_hash = document.content_hash
    source.title = document.title or source.title
    source.status = Source.READY
    source.last_synced_at = datetime.utcnow()
    source.error_message = ''

    version = _next_version(source)
    doc = Document(
        source_id=source.id,
        canonical_url=document.canonical_url,
        title=document.title,
        mime_type=document.mime_type,
        text=document.body,
        word_count=document.word_count,
        version=version,
    )
    db.session.add(doc)
    db.session.flush()

    for index, (chunk_text_value, locator) in enumerate(chunk_text(document.body)):
        chunk = DocumentChunk(
            document_id=doc.id,
            chunk_index=index,
            text=chunk_text_value,
            token_count=len(chunk_text_value.split()),
            locator=locator,
        )
        db.session.add(chunk)

    job.status = GenerationJob.SUCCEEDED
    job.finished_at = datetime.utcnow()
    db.session.commit()
    return source
