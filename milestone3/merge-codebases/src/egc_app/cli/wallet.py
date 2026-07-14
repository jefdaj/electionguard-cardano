import click
from egc_app.cli.utils import RoleAwareGroup
from egc_app.client import Client
from egc import *

@click.group(cls=RoleAwareGroup)
def wallet() -> None:
    "Basic wallet management for elections."

@click.option('--name', type=click.STRING, required=True)
@wallet.command()
def create(name):
    "Generate wallet."
    asyncio.run(Client().wallet_create(name))

@wallet.command()
def show():
    "Show wallet, except the signing key."
    resp = asyncio.run(Client().wallet_show())
    click.echo(json.dumps(resp, indent=2))

@wallet.command()
def load():
    "Load wallet from (.sk, .addr) files."
    raise NotImplementedError

@wallet.command()
def save():
    "Save wallet to (.sk, .addr) files."
    raise NotImplementedError

@wallet.command()
def clear():
    "Clear wallet, leaving files."
    asyncio.run(Client().wallet_clear())
