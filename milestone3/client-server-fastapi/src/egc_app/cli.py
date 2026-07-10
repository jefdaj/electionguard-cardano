import click
import asyncio
import uvicorn

from egc_app.client import Client
# from egc_app.server.run import run_server

import logging
LOG = logging.getLogger(__name__)


### main ###

@click.group()
def cli() -> None:
	pass

if __name__ == '__main__':
    cli()


### server ###

@cli.group()
def server() -> None:
	pass

@server.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--workers", default=1, type=int)
@click.option("--log-level", default="info")
def start(host, port, workers, log_level):
    """Run the API server."""
    uvicorn.run(
        "egc_app.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        workers=1, # TODO more for production?
        log_level=log_level,
    )

@server.command()
def health():
    """Is the server OK?"""
    resp = asyncio.run(Client().health())
    click.echo(resp)


### election ###

@cli.group()
def election() -> None:
	pass

@election.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--slot-no', type=click.INT)
@click.option('--block-header-hash', type=click.STRING)
def set(policy_id, slot_no, block_header_hash):
    """Set which election the server is following."""
    resp = asyncio.run(Client().set_election(policy_id, slot_no, block_header_hash))
    click.echo(resp)

@election.command()
@click.option('--filter', type=click.STRING, required=False)
def observe(filter: str|None = None):
    """Stream election events to the terminal."""
    async def _run():
        async for event in Client().stream_events(filter):
            click.echo(event)
    asyncio.run(_run())
