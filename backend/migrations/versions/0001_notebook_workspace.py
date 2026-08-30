"""Notebook workspace: workspaces, sources, documents, chunks, artifacts, jobs, notes, queries.

Revision ID: 0001_notebook_workspace
Revises:
Create Date: 2026-08-30
"""
from alembic import op
import sqlalchemy as sa


revision = '0001_notebook_workspace'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'workspaces',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_workspaces_user_id', 'workspaces', ['user_id'])

    op.create_table(
        'sources',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('url', sa.String(length=2048), nullable=False),
        sa.Column('title', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('source_type', sa.String(length=40), nullable=False, server_default='web'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('content_hash', sa.String(length=64), nullable=False, server_default=''),
        sa.Column('error_message', sa.Text(), nullable=False, server_default=''),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_sources_workspace_id', 'sources', ['workspace_id'])
    op.create_index('ix_sources_status', 'sources', ['status'])
    op.create_index('ix_sources_content_hash', 'sources', ['content_hash'])

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('source_id', sa.Integer(),
                  sa.ForeignKey('sources.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('canonical_url', sa.String(length=2048), nullable=False, server_default=''),
        sa.Column('title', sa.String(length=512), nullable=False, server_default=''),
        sa.Column('mime_type', sa.String(length=120), nullable=False,
                  server_default='text/plain'),
        sa.Column('text', sa.Text(), nullable=False, server_default=''),
        sa.Column('word_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint('source_id', 'version', name='uq_documents_source_version'),
    )
    op.create_index('ix_documents_source_id', 'documents', ['source_id'])

    op.create_table(
        'document_chunks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('document_id', sa.Integer(),
                  sa.ForeignKey('documents.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False, server_default=''),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locator', sa.String(length=255), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.UniqueConstraint('document_id', 'chunk_index', name='uq_chunks_doc_index'),
    )
    op.create_index('ix_document_chunks_document_id', 'document_chunks', ['document_id'])

    op.create_table(
        'artifacts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('artifact_type', sa.String(length=40), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('instructions', sa.Text(), nullable=False, server_default=''),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('error_message', sa.Text(), nullable=False, server_default=''),
        sa.Column('schema_version', sa.String(length=20), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_artifacts_workspace_id', 'artifacts', ['workspace_id'])
    op.create_index('ix_artifacts_artifact_type', 'artifacts', ['artifact_type'])
    op.create_index('ix_artifacts_status', 'artifacts', ['status'])

    op.create_table(
        'artifact_sources',
        sa.Column('artifact_id', sa.Integer(),
                  sa.ForeignKey('artifacts.id', ondelete='CASCADE'),
                  primary_key=True),
        sa.Column('source_id', sa.Integer(),
                  sa.ForeignKey('sources.id', ondelete='CASCADE'),
                  primary_key=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )

    op.create_table(
        'generation_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('artifact_id', sa.Integer(),
                  sa.ForeignKey('artifacts.id', ondelete='SET NULL'),
                  nullable=True),
        sa.Column('job_type', sa.String(length=40), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('payload', sa.Text(), nullable=False, server_default='{}'),
        sa.Column('result', sa.Text(), nullable=False, server_default=''),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('error_message', sa.Text(), nullable=False, server_default=''),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_generation_jobs_workspace_id', 'generation_jobs', ['workspace_id'])
    op.create_index('ix_generation_jobs_artifact_id', 'generation_jobs', ['artifact_id'])
    op.create_index('ix_generation_jobs_job_type', 'generation_jobs', ['job_type'])
    op.create_index('ix_generation_jobs_status', 'generation_jobs', ['status'])

    op.create_table(
        'workspace_notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_workspace_notes_workspace_id', 'workspace_notes', ['workspace_id'])
    op.create_index('ix_workspace_notes_status', 'workspace_notes', ['status'])

    op.create_table(
        'queries',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('workspace_id', sa.Integer(),
                  sa.ForeignKey('workspaces.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('job_id', sa.Integer(),
                  sa.ForeignKey('generation_jobs.id', ondelete='SET NULL'),
                  nullable=True, unique=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('answer', sa.Text(), nullable=False, server_default=''),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('citations', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('source_ids', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('note_ids', sa.Text(), nullable=False, server_default='[]'),
        sa.Column('error_message', sa.Text(), nullable=False, server_default=''),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                  server_default=sa.func.current_timestamp()),
    )
    op.create_index('ix_queries_workspace_id', 'queries', ['workspace_id'])
    op.create_index('ix_queries_status', 'queries', ['status'])


def downgrade():
    op.drop_table('queries')
    op.drop_table('workspace_notes')
    op.drop_table('generation_jobs')
    op.drop_table('artifact_sources')
    op.drop_table('artifacts')
    op.drop_table('document_chunks')
    op.drop_table('documents')
    op.drop_table('sources')
    op.drop_table('workspaces')
