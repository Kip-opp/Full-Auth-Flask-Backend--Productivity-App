"""Artifact provider boundary.

The default :class:`LocalArtifactProvider` returns deterministic
template-shaped JSON so the API and UI work without any external
credentials. A real provider (e.g. an OpenAI or Anthropic adapter) is
expected to inherit the same :class:`ArtifactProvider` contract and to
attach source IDs to every claim, row, bullet, or answer.
"""
from __future__ import annotations

import json
from typing import Dict, List, Protocol


SCHEMA_VERSION = '1.0'


class ArtifactProvider(Protocol):
    """Contract every artifact provider must satisfy."""

    def generate(self, artifact_type: str, title: str,
                 instructions: str,
                 evidence: List[Dict]) -> Dict:
        """Return structured JSON for the requested artifact type.

        ``evidence`` is a list of dicts with at least ``kind``,
        ``source_id`` or ``note_id``, ``title``, ``locator``, and
        ``excerpt``. The provider must not invent identifiers that are
        not in the evidence list.
        """


class LocalArtifactProvider:
    """Deterministic, extractive provider for local development."""

    def generate(self, artifact_type: str, title: str,
                 instructions: str,
                 evidence: List[Dict]) -> Dict:
        citations = self._build_citations(evidence)
        evidence_excerpts = [self._excerpt(e.get('excerpt', '')) for e in evidence]

        if artifact_type == 'slides':
            return self._slides(title, instructions, evidence, citations, evidence_excerpts)
        if artifact_type == 'mindmap':
            return self._mindmap(title, evidence, citations)
        if artifact_type == 'table':
            return self._table(title, evidence, citations, evidence_excerpts)
        if artifact_type == 'quiz':
            return self._quiz(title, instructions, evidence, citations)
        if artifact_type == 'summary':
            return self._summary(title, instructions, evidence, citations, evidence_excerpts)
        raise ValueError(f'Unsupported artifact type: {artifact_type}')

    @staticmethod
    def _excerpt(text: str, limit: int = 240) -> str:
        text = (text or '').strip()
        if len(text) <= limit:
            return text
        return text[: limit - 1].rstrip() + '…'

    @staticmethod
    def _build_citations(evidence: List[Dict]) -> List[Dict]:
        return [
            {
                'source_id': e.get('source_id'),
                'note_id': e.get('note_id'),
                'title': e.get('title', ''),
                'locator': e.get('locator', ''),
            }
            for e in evidence
        ]

    def _slides(self, title, instructions, evidence, citations, excerpts):
        bullets: List[str] = excerpts or [instructions or 'No source content available.']
        # Pad to a minimum of three slides so the UI has something to show.
        while len(bullets) < 3:
            bullets.append('Add a source to populate this slide.')
        slides = []
        for i, bullet in enumerate(bullets[:8], start=1):
            slide = {
                'slide_number': i,
                'title': title if i == 1 else f'{title} (cont.)' if i == len(bullets) else f'Slide {i}',
                'bullets': [bullet] if isinstance(bullet, str) else bullet,
                'speaker_notes': f'Source {evidence[i - 1].get("source_id") or evidence[i - 1].get("note_id")}' if i - 1 < len(evidence) else '',
                'citations': [evidence[i - 1].get('source_id')] if i - 1 < len(evidence) and evidence[i - 1].get('source_id') else [],
            }
            slides.append(slide)
        return {
            'schema_version': SCHEMA_VERSION,
            'title': title,
            'slides': slides,
            'citations': citations,
        }

    def _mindmap(self, title, evidence, citations):
        children = []
        for e in evidence:
            label = e.get('title') or 'Untitled'
            detail = self._excerpt(e.get('excerpt', ''), 140)
            child = {
                'label': label[:80],
                'detail': detail,
            }
            if e.get('source_id') is not None:
                child['source_id'] = e['source_id']
            if e.get('note_id') is not None:
                child['note_id'] = e['note_id']
            children.append(child)
        if not children:
            children = [{'label': 'Add a source to begin', 'detail': ''}]
        return {
            'schema_version': SCHEMA_VERSION,
            'root': title,
            'children': children,
            'citations': citations,
        }

    def _table(self, title, evidence, citations, excerpts):
        rows = [[e.get('title', ''), self._excerpt(e.get('excerpt', ''), 120)]
                for e in evidence]
        if not rows:
            rows = [['No sources', 'Add a source to populate this table.']]
        return {
            'schema_version': SCHEMA_VERSION,
            'title': title,
            'columns': ['Source', 'Excerpt'],
            'rows': rows,
            'citations': citations,
        }

    def _quiz(self, title, instructions, evidence, citations):
        questions = []
        for idx, e in enumerate(evidence, start=1):
            options = [
                self._excerpt(e.get('excerpt', ''), 80) or 'Option A',
                'Not stated in the sources',
                'A different source',
                'Unknown',
            ]
            question = {
                'id': idx,
                'question': f"According to {e.get('title') or 'this source'}, what is the main idea?",
                'options': options,
                'answer_index': 0,
                'explanation': f"Grounded in {e.get('title') or 'this source'}.",
            }
            if e.get('source_id') is not None:
                question['source_id'] = e['source_id']
            if e.get('note_id') is not None:
                question['note_id'] = e['note_id']
            questions.append(question)
        if not questions:
            questions = [{
                'id': 1,
                'question': 'No sources are available yet. Add a source and try again.',
                'options': ['OK'],
                'answer_index': 0,
                'explanation': '',
            }]
        return {
            'schema_version': SCHEMA_VERSION,
            'title': title,
            'instructions': instructions or 'Answer each question using only the provided sources.',
            'questions': questions,
            'citations': citations,
        }

    def _summary(self, title, instructions, evidence, citations, excerpts):
        body_parts = [self._excerpt(e.get('excerpt', ''), 280) for e in evidence]
        body_parts = [b for b in body_parts if b]
        if not body_parts:
            body = 'No source content was found. Add a source and try again.'
        else:
            body = ' '.join(body_parts)
        return {
            'schema_version': SCHEMA_VERSION,
            'title': title,
            'summary': body,
            'instructions': instructions,
            'citations': citations,
        }


def validate_artifact_content(artifact_type: str, payload: Dict) -> Dict:
    """Best-effort validation of provider output. Returns a sanitized dict."""
    if not isinstance(payload, dict):
        raise ValueError('Provider output must be a JSON object')
    payload.setdefault('schema_version', SCHEMA_VERSION)
    expected_keys = {
        'slides': {'slides'},
        'mindmap': {'root', 'children'},
        'table': {'columns', 'rows'},
        'quiz': {'questions'},
        'summary': {'summary'},
    }
    required = expected_keys.get(artifact_type, set())
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f'Provider output missing keys: {sorted(missing)}')
    return payload
