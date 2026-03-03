import click

from ecf.service import EcfService


def register_cli(app):
    @app.cli.command("ecf_process_pending")
    @click.option("--limit", default=50, show_default=True, type=int)
    def ecf_process_pending(limit: int):
        """Procesa documentos e-CF pendientes (modo cron/cPanel)."""
        results = EcfService.process_pending(limit=limit)
        click.echo(f"Procesados: {len(results)}")
        for item in results:
            click.echo(f"#{item['id']} -> {item['status']} :: {item['message']}")
