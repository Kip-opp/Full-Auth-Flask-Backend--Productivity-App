"""Artifact generation service.

Builds the evidence bundle from ready sources, calls the configured
:class:`ArtifactProvider`, and writes the resulting JSON onto the
:class:`Artifact` record together with the source provenance join rows.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional

from app.extensions import db
from app.models.artifact import Artifact, ArtifactSource
from app.models.document import Document, DocumentChunk
from app.models.job import GenerationJob
from app.models.source import Source
from app.services.artifact_providers import (
    LocalArtifactProvider,
    validate_artifact_content,
)


DEFAULT_EVIDENCE_LIMIT = 8
MAX_EVIDENCE_EXCERPT_CHARS = 1200


def _select_evidence(source_ids: List[int], *,
                     evidence_limit: int = DEFAULT_EVIDENCE_LIMIT) -> List[Dict]:
    """Build the deterministic evidence bundle for artifact generation."""
    if not source_ids:
        return []
    sources = (
        Source.query
        .filter(Source.id.in_(source_ids), Source.status == Source.READY)
        .all()
    )
    sources.sort(key=lambda s: source_ids.index(s.id))
    evidence: List[Dict] = []
    for source in sources:
        document = (
            Document.query.filter_by(source_id=source.id)
            .order_by(Document.version.desc())
            .first()
        )
        if not document:
            continue
        chunks = (
            DocumentChunk.query.filter_by(document_id=document.id)
            .order_by(DocumentChunk.chunk_index.asc())
            .limit(evidence_limit)
            .all()
        )
        if not chunks:
            evidence.append({
                'kind': 'source',
                'source_id': source.id,
                'title': source.title or source.url,
                'locator': document.canonical_url or source.url,
                'excerpt': document.text[:MAX_EVIDENCE_EXCERPT_CHARS],
            })
        else:
            for chunk in chunks:
                evidence.append({
                    'kind': 'source',
                    'source_id': source.id,
                    'title': source.title or source.url,
                    'locator': chunk.locator or document.canonical_url or source.url,
                    'excerpt': chunk.text[:MAX_EVIDENCE_EXCERPT_CHARS],
                })
        if len(evidence) >= evidence_limit:
            break
    return evidence[:evidence_limit]


def run_artifact_generation(job: GenerationJob,
                            provider: Optional[LocalArtifactProvider] = None
                            ) -> Artifact:
    """Execute an ``artifact_generation`` job and persist the result."""
    payload = json.loads(job.payload or '{}')
    artifact_id = payload.get('artifact_id')
    artifact: Optional[Artifact] = None
    if artifact_id is not None:
        artifact = Artifact.query.get(artifact_id)
    if artifact is None:
        raise RuntimeError('Artifact not found for generation job')

    artifact.status = Artifact.RUNNING
    artifact.error_message = ''
    db.session.commit()

    source_ids = sorted({link.source_id for link in artifact.sources})
    evidence = _select_evidence(source_ids)

    provider = provider or LocalArtifactProvider()
    try:
        result = provider.generate(
            artifact.artifact_type,
            artifact.title,
            artifact.instructions,
            evidence,
        )
        result = validate_artifact_content(artifact.artifact_type, result)
    except Exception as exc:  # noqa: BLE001
        artifact.status = Artifact.FAILED
        artifact.error_message = 'Generation failed'[:500]
        job.status = GenerationJob.FAILED
        job.error_message = artifact.error_message
        job.finished_at = datetime.utcnow()
        db.session.commit()
        raise

    artifact.content = json.dumps(result)
    artifact.schema_version = result.get('schema_version', '1.0')
    artifact.status = Artifact.SUCCEEDED
    artifact.error_message = ''

    job.status = GenerationJob.SUCCEEDED
    job.finished_at = datetime.utcnow()
    db.session.commit()
    return artifact
