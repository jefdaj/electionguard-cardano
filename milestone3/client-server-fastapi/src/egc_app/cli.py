import click
import asyncio
import uvicorn

from egc_app.client import Client
# from egc_app.server.run import run_server

import logging
LOG = logging.getLogger(__name__)

@click.group()
def cli() -> None:
	pass

@cli.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--reload", is_flag=True, help="Auto-reload on code changes (dev only).")
@click.option("--workers", default=1, type=int)
@click.option("--log-level", default="info")
def serve(host, port, reload, workers, log_level):
    """Run the API server."""
    if reload and workers > 1:
        raise click.UsageError("--reload is incompatible with --workers > 1.")

    uvicorn.run(
        "egc_app.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )

# old code for reference:
# @cli.command()
# def serve():
#     run_server()

@cli.command()
def health():
    resp = asyncio.run(Client().health())
    click.echo(resp)

# TODO remove
@cli.command()
@click.argument("n", type=int, required=False)
def trivial(n: int | None):
    # LOG.debug('incr')
    # LOG.debug(f'n: {n}')
    if n is None:
        n = asyncio.run(Client().get_trivial())
    else:
        n = asyncio.run(Client().set_trivial(n))
    click.echo(n)

@cli.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--slot-no', type=click.INT)
@click.option('--block-header-hash', type=click.STRING)
def subscribe(policy_id, slot_no, block_header_hash):
    resp = asyncio.run(Client().subscribe(policy_id, slot_no, block_header_hash))
    click.echo(resp)

@cli.command()
@click.option('--policy-id', type=click.STRING, required=True)
def observe(policy_id: str):
    # events = asyncio.run(Client().observe(policy_id))
    # click.echo(events)
    async def _run():
        async for event in Client().observe(policy_id):
            click.echo(event)
    asyncio.run(_run())

# TODO init_election

if __name__ == '__main__':
    cli()
