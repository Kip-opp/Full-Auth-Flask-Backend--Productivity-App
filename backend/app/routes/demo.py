"""Public, read-only demo content for unauthenticated visitors."""
from flask import Blueprint

from app.utils.responses import success_response


demo_bp = Blueprint('demo', __name__, url_prefix='/api/demo')


@demo_bp.route('/workspace', methods=['GET'])
def demo_workspace():
    """Return a fixed workspace snapshot without exposing private records."""
    return success_response(
        data={
            'workspace': {
                'id': 'demo',
                'name': 'Notebook demo',
                'description': 'A read-only tour of a source-grounded workspace.',
            },
            'sources': [
                {
                    'id': 'demo-source-1',
                    'url': 'https://www.nasa.gov/learning-resources/for-kids-and-students/',
                    'title': 'NASA learning resources',
                    'source_type': 'web',
                    'status': 'ready',
                    'error_message': '',
                },
                {
                    'id': 'demo-source-2',
                    'url': 'https://www.w3.org/WAI/fundamentals/accessibility-intro/',
                    'title': 'Introduction to web accessibility',
                    'source_type': 'web',
                    'status': 'ready',
                    'error_message': '',
                },
            ],
            'notes': [
                {
                    'id': 'demo-note-1',
                    'title': 'A useful research habit',
                    'content': 'Start with a small set of trustworthy sources, then capture the claims you want to revisit.',
                    'status': 'active',
                },
            ],
            'queries': [
                {
                    'id': 'demo-query-1',
                    'question': 'What makes a source useful for a notebook?',
                    'answer': 'A useful source is relevant to the question, clear about its evidence, and easy to revisit. A notebook keeps those sources connected to notes and citations.',
                    'status': 'succeeded',
                    'citations': [
                        {'source_id': 'demo-source-1', 'title': 'NASA learning resources', 'locator': 'Learning resources'},
                        {'source_id': 'demo-source-2', 'title': 'Introduction to web accessibility', 'locator': 'Accessibility fundamentals'},
                    ],
                },
            ],
            'artifacts': [
                {
                    'id': 'demo-artifact-1',
                    'artifact_type': 'summary',
                    'title': 'Demo summary',
                    'status': 'succeeded',
                    'content': '{"summary":"A good notebook makes trusted sources easier to understand, revisit, and connect to your own thinking."}',
                    'error_message': '',
                },
            ],
        },
        message='Demo workspace retrieved successfully',
    )