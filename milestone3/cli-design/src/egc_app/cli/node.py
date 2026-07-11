import click
import asyncio
import uvicorn
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup
from egc_app.server.run import run as run_server

@click.group(cls=RoleAwareGroup)
def node() -> None:
    "Start, stop, or check status of your node."

@node.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--dev-mode", is_flag=True, default=False)
def run(host, port, dev_mode):
    "Run the EGC node (API server)."
    run_server(**locals())

@node.command()
def config():
    "Get the current node config."
    resp = asyncio.run(Client().node_config())
    click.echo(resp)

@node.command()
def status():
    "Is the node OK?"
    resp = asyncio.run(Client().node_status())
    click.echo(resp)

@node.command()
def stop():
    "Stop the node gracefully."
    raise NotImplementedError
