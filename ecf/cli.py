import logging

import click

from ecf.tasks import process_pending


logger = logging.getLogger(__name__)


def register_cli(app):
    @app.cli.command("ecf_process_pending")
    @click.option("--limit", default=50, show_default=True, type=int)
    def ecf_process_pending(limit: int):
        """Procesa documentos e-CF pendientes (cron/cPanel)."""
        summary = process_pending(limit=limit)
        logger.info("ecf_process_pending summary=%s", summary)
        click.echo("e-CF pending processing")
        click.echo(f"processed:   {summary['processed']}")
        click.echo(f"accepted:    {summary['accepted']}")
        click.echo(f"conditional: {summary['conditional']}")
        click.echo(f"rejected:    {summary['rejected']}")
        click.echo(f"processing:  {summary['processing']}")
        click.echo(f"errors:      {summary['errors']}")
