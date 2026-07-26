import click
import asyncio
import json
import uvicorn
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup
from egc_app.server.run import run as run_server

@click.group(cls=RoleAwareGroup)
def node() -> None:
    "Start, stop, await, check status of your node."

@node.command()
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
@click.option("--dev-mode", is_flag=True, default=False)
@click.option("--private-dir", type=click.STRING, required=True) # TODO click.PATH?
def run(host, port, dev_mode, private_dir):
    "Run the EGC node (API server)."
    # print(locals())
    run_server(**locals())

# TODO pick: egc node config (here)? or egc config node?
# @node.command()
# def config():
#     "Get the current node config."
#     resp = asyncio.run(Client().config())
#     click.echo(json.dumps(resp, indent=2))

@node.command()
def status():
    "Is the node OK?"
    # TODO add Kubo + Ogmios status too
    resp = asyncio.run(Client().node_status())
    click.echo(resp)

@node.command(name="await")
def await_():
    """Wait until the node is stable.

    Only waits for the IPFS (Kubo) node so far.
    """
    # TODO add Ogmios too
    asyncio.run(Client().node_await())
    # click.echo(resp)

@node.command()
def stop():
    "Stop the node gracefully."
    raise NotImplementedError
