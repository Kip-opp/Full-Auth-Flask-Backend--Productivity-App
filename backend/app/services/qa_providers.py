"""Q&A provider boundary.

The default :class:`LocalQuestionAnswerProvider` is extractive: it
returns a grounded snippet from the top-ranked evidence and refuses to
fabricate URLs, source IDs, or locators that are not in the evidence
bundle. A real model adapter must implement the same contract and
validate that every citation it emits refers to a retrieved evidence
item.
"""
from __future__ import annotations

from typing import Dict, List, Protocol


INSUFFICIENT_EVIDENCE = (
    'The notebook does not contain enough evidence to answer that question '
    'with confidence. Add a source or write a notebook note with the '
    'relevant details and try again.'
)


class QuestionAnswerProvider(Protocol):
    """Contract for Q&A providers."""

    def answer(self, question: str, evidence: List[Dict]) -> Dict:
        """Return ``{"answer": str, "citations": list[dict]}``."""


class LocalQuestionAnswerProvider:
    """Deterministic extractive provider used for local development."""

    MAX_EXCERPT_CHARS = 480

    def answer(self, question: str, evidence: List[Dict]) -> Dict:
        if not evidence:
            return {'answer': INSUFFICIENT_EVIDENCE, 'citations': []}

        scored = [(self._score(question, e), e) for e in evidence]
        scored.sort(key=lambda pair: pair[0], reverse=True)

        best_score, best = scored[0]
        if best_score <= 0:
            return {'answer': INSUFFICIENT_EVIDENCE, 'citations': []}

        excerpt = (best.get('excerpt') or '').strip()
        excerpt = excerpt[: self.MAX_EXCERPT_CHARS]
        if not excerpt:
            return {'answer': INSUFFICIENT_EVIDENCE, 'citations': []}

        citation = {
            'kind': best.get('kind', 'source'),
            'source_id': best.get('source_id'),
            'note_id': best.get('note_id'),
            'title': best.get('title', ''),
            'locator': best.get('locator', ''),
        }
        answer = (
            f"{excerpt}\n\n"
            f"Source: {citation['title'] or 'untitled'}"
        )
        return {'answer': answer, 'citations': [citation]}

    @staticmethod
    def _score(question: str, evidence: Dict) -> int:
        question_terms = {
            token.lower().strip('.,!?:;()[]"\'')
            for token in question.split()
            if len(token) > 2
        }
        excerpt = (evidence.get('excerpt') or '').lower()
        return sum(1 for term in question_terms if term and term in excerpt)
