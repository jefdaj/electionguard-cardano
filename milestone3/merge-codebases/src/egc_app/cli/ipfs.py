import click
# import cloup
# from cloup.constraints import RequireExactly
import asyncio
# from egc import ElectionConfig, scan_qrcode, print_qrcode # TODO relative?
from egc_app.client import Client
from egc_app import schemas
from egc_app.cli.utils import *
from egc import *

@click.group(cls=RoleAwareGroup)
def ipfs() -> None:
    "Show and post explicit IPFS peers."

# TODO resolve: are you showing your own node, the list of subscribed ones, or both?

@ipfs.command()
def show():
    """Print your current IPFS channel nodes (explicit peers mentioned in the
    election state) as JSON, as well as your own node info. Use jq to access
    fields if needed.
    """
    cfg = asyncio.run(Client().ipfs_show())
    click.echo(json.dumps(cfg))

@ipfs.command(roles=['admin', 'guardian', 'device', 'verifier'])
def post():
    "Post your current IPFS contact info to your channel state."
    asyncio.run(Client().ipfs_post())
