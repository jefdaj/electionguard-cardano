import click
import json
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
    asyncio.run(Client().wallet_load_or_create(name, sk_dict=None))

@wallet.command()
def show():
    "Show wallet, except the signing key."
    resp = asyncio.run(Client().wallet_show())
    click.echo(json.dumps(resp, indent=2))

@wallet.command()
def clear():
    "Clear wallet, leaving files."
    asyncio.run(Client().wallet_clear())

@click.option('--sk-path', type=click.STRING, required=True)
@wallet.command()
def load(sk_path):
    "Load wallet from a local .sk file."
    sk_path = Path(sk_path).absolute()
    with sk_path.open('r') as f:
        sk_dict = json.load(f)
    asyncio.run(Client().wallet_load_or_create(
        name    = sk_path.stem,
        sk_dict = sk_dict
    ))

@click.option('--sk-path', type=click.STRING, required=True)
@wallet.command()
def save(sk_path):
    "Save wallet to a local .sk file."
    sk_path = Path(sk_path)
    sk_json = asyncio.run(Client().wallet_save())
    if sk_path.exists():
        raise Exception(f'sk_path exists: {sk_path}')
    with sk_path.open('w') as f:
        f.write(sk_json) # already json; no dump needed
    click.echo(f"Saved wallet → {sk_path}")
