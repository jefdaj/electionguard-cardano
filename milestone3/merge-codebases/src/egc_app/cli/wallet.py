import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *
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

# @click.option('--sk-path', type=click.STRING, required=True)
@wallet.command()
@payload_io("qr", "qr-image", "json", direction="in")
def load(**pio_args):
    """Load wallet.

    Note that .sk files can be loaded with the JSON option.
    """
    pio = resolve_payload("in", **pio_args)
    print(f'pio: {pio}')
    return # TODO finish
    sk_path = Path(sk_path).absolute()
    with sk_path.open('r') as f:
        sk_dict = json.load(f)
    asyncio.run(Client().wallet_load_or_create(
        name    = sk_path.stem,
        sk_dict = sk_dict
    ))

# @click.option('--sk-path', type=click.STRING, required=True)
@wallet.command()
@payload_io("qr", "qr-image", "json", direction="out")
def save(**pio_args):
    """Save wallet, INCLUDING THE SIGNING KEY.

    Note that .sk files can be saved with the JSON option.
    """
    print(f'pio_args: {pio_args}')
    pio = resolve_payload("out", **pio_args) # TODO direction?
    print(f'pio: {pio}')
    return # TODO finish
    sk_path = Path(sk_path)
    sk_json = asyncio.run(Client().wallet_save())
    if sk_path.exists():
        raise Exception(f'sk_path exists: {sk_path}')
    with sk_path.open('w') as f:
        f.write(sk_json) # already json; no dump needed
    click.echo(f"Saved wallet → {sk_path}")
