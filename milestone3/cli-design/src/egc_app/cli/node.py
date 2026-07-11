import click
import asyncio
import uvicorn
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def node() -> None:
    "Start, stop, or check status of your node."

@node.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--workers", default=1, type=int)
@click.option("--log-level", default="info")
def run(host, port, workers, log_level):
    "Run the node (API server)."
    uvicorn.run(
        "egc_app.server.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=True,
        workers=1, # TODO more for production?
        log_level=log_level,
    )

@node.command()
def status():
    "Is the node OK?"
    resp = asyncio.run(Client().node_status())
    click.echo(resp)

@node.command()
def stop():
    "Stop the node gracefully."
    raise NotImplementedError
