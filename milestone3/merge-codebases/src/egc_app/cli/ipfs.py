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
@click.option('--explicit-hints', type=click.STRING, required=False, multiple=True)
@click.option('--n-global-hints', type=click.INT, default=8)
@click.option('--n-local-hints', type=click.INT, default=0)
def post(explicit_hints: list[str], n_global_hints: int, n_local_hints: int):
    """Post your current IPFS contact info to your channel state. Always
    includes your peer_id. Can optionally also include explicit relays or addr
    hints, or auto-generate them to optimize for global and/or local
    connectivity."""
    n_total = len(explicit_hints) + n_global_hints + n_local_hints
    if n_total > 8:
        raise Exception('Max 8 hints allowed by contract')
    asyncio.run(Client().ipfs_post(
        explicit_hints = explicit_hints,
        n_global_hints = n_global_hints,
        n_local_hints = n_local_hints,
    ))
