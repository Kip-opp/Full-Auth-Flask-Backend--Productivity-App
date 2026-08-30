"""Flask CLI commands for the local worker and database bootstrap."""
import click
from flask.cli import with_appcontext

from app.extensions import db
from app.services.job_worker import run_batch


def register_cli(app):
    @app.cli.command('worker')
    @click.option('--workspace-id', type=int, default=None,
                  help='Restrict the run to a single workspace (for testing).')
    @click.option('--limit', type=int, default=25,
                  help='Maximum number of jobs to process in this batch.')
    @with_appcontext
    def worker(workspace_id, limit):
        """Process a bounded batch of queued jobs."""
        jobs = run_batch(workspace_id=workspace_id, limit=limit)
        if not jobs:
            click.echo('No queued jobs.')
            return
        for job in jobs:
            click.echo(f"job={job.id} type={job.job_type} status={job.status}")
        click.echo(f'Processed {len(jobs)} job(s).')
