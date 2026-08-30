"""Notebook Q&A service.

Implements the retrieval and provider boundary for the Ask-notebook
feature. Evidence is loaded only from sources and notes that belong to
the requesting workspace. The local retrieval strategy is deterministic
lexical ranking with a stable limit; production should swap in a
hybrid vector+BM25 adapter without changing this contract.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from app.extensions import db
from app.models.document import Document, DocumentChunk
from app.models.job import GenerationJob
from app.models.notebook import Query, WorkspaceNote
from app.models.source import Source
from app.services.qa_providers import (
    INSUFFICIENT_EVIDENCE,
    LocalQuestionAnswerProvider,
    QuestionAnswerProvider,
)


DEFAULT_EVIDENCE_LIMIT = 6
MAX_EXCERPT_CHARS = 1000


def _tokenize(text: str) -> List[str]:
    return [
        token.lower().strip('.,!?:;()[]"\'')
        for token in (text or '').split()
        if len(token) > 2
    ]


def _score_excerpt(question_tokens: Sequence[str], excerpt: str) -> int:
    haystack = (excerpt or '').lower()
    if not haystack:
        return 0
    return sum(1 for term in question_tokens if term in haystack)


def _normalize_ids(values) -> List[int]:
    seen: List[int] = []
    for v in values or []:
        try:
            i = int(v)
        except (TypeError, ValueError):
            continue
        if i not in seen:
            seen.append(i)
    return seen


def collect_evidence(workspace_id: int,
                     *,
                     source_ids: Optional[Sequence[int]] = None,
                     note_ids: Optional[Sequence[int]] = None,
                     evidence_limit: int = DEFAULT_EVIDENCE_LIMIT) -> List[Dict]:
    """Return the ranked evidence bundle for a workspace question.

    If ``source_ids`` is empty or ``None``, every ``ready`` source in the
    workspace is considered. The same rule applies to ``note_ids`` with
    active notes. Cross-workspace IDs are silently dropped — validation
    that all supplied IDs belong to the workspace happens upstream in
    the route.
    """
    evidence: List[Dict] = []
    if source_ids:
        sources = (
            Source.query
            .filter(Source.id.in_(source_ids),
                    Source.workspace_id == workspace_id,
                    Source.status == Source.READY)
            .all()
        )
    else:
        sources = (
            Source.query
            .filter(Source.workspace_id == workspace_id,
                    Source.status == Source.READY)
            .order_by(Source.updated_at.desc())
            .all()
        )

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
            .all()
        )
        for chunk in chunks:
            evidence.append({
                'kind': 'source',
                'source_id': source.id,
                'title': source.title or source.url,
                'locator': chunk.locator or document.canonical_url or source.url,
                'url': source.url,
                'excerpt': chunk.text[:MAX_EXCERPT_CHARS],
            })

    if note_ids:
        notes = (
            WorkspaceNote.query
            .filter(WorkspaceNote.id.in_(note_ids),
                    WorkspaceNote.workspace_id == workspace_id,
                    WorkspaceNote.status == WorkspaceNote.ACTIVE)
            .all()
        )
    else:
        notes = (
            WorkspaceNote.query
            .filter(WorkspaceNote.workspace_id == workspace_id,
                    WorkspaceNote.status == WorkspaceNote.ACTIVE)
            .order_by(WorkspaceNote.updated_at.desc())
            .all()
        )

    for note in notes:
        evidence.append({
            'kind': 'note',
            'note_id': note.id,
            'title': note.title,
            'locator': f'note:{note.id}',
            'excerpt': note.content[:MAX_EXCERPT_CHARS],
        })

    return evidence[: max(evidence_limit, 1) * 4]  # Keep top items for ranking


def rank_evidence(question: str, evidence: List[Dict], limit: int) -> List[Dict]:
    """Deterministic lexical ranking with a stable tie-break."""
    tokens = _tokenize(question)
    scored = [(_score_excerpt(tokens, e.get('excerpt', '')), idx, e)
              for idx, e in enumerate(evidence)]
    scored.sort(key=lambda t: (t[0], -t[1]), reverse=True)
    return [item for score, _, item in scored[:limit] if score > 0]


def run_query_job(query: Query,
                  provider: Optional[QuestionAnswerProvider] = None) -> Query:
    """Execute a question-answering job and persist the answer."""
    if query.job_id is None:
        raise RuntimeError('Query is not associated with a job')

    job: Optional[GenerationJob] = GenerationJob.query.get(query.job_id)
    if job is None:
        raise RuntimeError('Query job not found')

    query.status = Query.RUNNING
    job.status = GenerationJob.RUNNING
    job.started_at = datetime.utcnow()
    db.session.commit()

    provider = provider or LocalQuestionAnswerProvider()

    try:
        source_ids = _normalize_ids(json.loads(query.source_ids or '[]'))
        note_ids = _normalize_ids(json.loads(query.note_ids or '[]'))
        evidence_pool = collect_evidence(
            query.workspace_id,
            source_ids=source_ids,
            note_ids=note_ids,
        )
        evidence = rank_evidence(query.question, evidence_pool, DEFAULT_EVIDENCE_LIMIT)
        result = provider.answer(query.question, evidence)
    except Exception:  # noqa: BLE001
        query.status = Query.FAILED
        query.error_message = 'Answer generation failed'[:500]
        job.status = GenerationJob.FAILED
        job.error_message = query.error_message
        job.finished_at = datetime.utcnow()
        db.session.commit()
        raise

    citations = result.get('citations') or []
    if not citations and not evidence:
        query.answer = INSUFFICIENT_EVIDENCE
    else:
        query.answer = result.get('answer') or INSUFFICIENT_EVIDENCE

    # Validate citations map to evidence before persisting.
    valid_ids = {
        ('source', e.get('source_id')) for e in evidence if e.get('source_id') is not None
    } | {
        ('note', e.get('note_id')) for e in evidence if e.get('note_id') is not None
    }
    safe_citations: List[Dict] = []
    for c in citations:
        kind = 'source' if c.get('source_id') is not None else 'note'
        ident = c.get('source_id') if kind == 'source' else c.get('note_id')
        if (kind, ident) in valid_ids:
            safe_citations.append({
                'kind': c.get('kind', kind),
                'source_id': c.get('source_id'),
                'note_id': c.get('note_id'),
                'title': c.get('title', ''),
                'locator': c.get('locator', ''),
            })
    if not safe_citations and evidence and result.get('answer') != INSUFFICIENT_EVIDENCE:
        # Always expose at least the top evidence as a citation so the
        # user can audit the answer.
        top = evidence[0]
        safe_citations.append({
            'kind': top.get('kind'),
            'source_id': top.get('source_id'),
            'note_id': top.get('note_id'),
            'title': top.get('title', ''),
            'locator': top.get('locator', ''),
        })

    query.citations = json.dumps(safe_citations)
    query.status = Query.SUCCEEDED
    query.error_message = ''

    job.status = GenerationJob.SUCCEEDED
    job.finished_at = datetime.utcnow()
    db.session.commit()
    return query
