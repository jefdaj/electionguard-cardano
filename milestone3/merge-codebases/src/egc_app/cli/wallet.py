import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *
from egc_app.schemas.wallet import WalletLoadOrCreate
from egc import *

@click.group(cls=RoleAwareGroup)
def wallet() -> None:
    "Basic wallet management for elections."

@click.option('--description', type=click.STRING, required=True)
@wallet.command()
def create(description):
    "Generate wallet."
    # asyncio.run(Client().wallet_load_or_create(description, sk_dict=None))
    description = description.replace(':', ';') # escape for possible qr str
    asyncio.run(Client().wallet_load_or_create(
        WalletLoadOrCreate(sk_or_desc=description)
    ))

@wallet.command()
def show():
    "Show wallet, except the signing key."
    resp = asyncio.run(Client().wallet_show())
    click.echo(json.dumps(resp, indent=2))

@wallet.command()
def clear():
    "Clear wallet, leaving files."
    asyncio.run(Client().wallet_clear())

@wallet.command()
@multi_load("wallet", Wallet, ["cam", "png", "txt", "json"])
def load(wallet: Wallet):
    """Load wallet.

    Note that .sk files can be loaded with the JSON option.
    """
    # print(f'wallet: {wallet}')
    # sk_dict = json.loads(wallet.to_json())
    # print(f'sk_dict from wallet: {sk_dict}')
    asyncio.run(Client().wallet_load_or_create(
        WalletLoadOrCreate(sk_or_desc=wallet.sk)
    ))

# @click.option('--sk-path', type=click.STRING, required=True)
@wallet.command()
@multi_save_arg("wallet", ["cam", "png", "txt", "json"])
def save(wallet: MultiIOArg):
    """Save wallet, INCLUDING THE SIGNING KEY.

    Note that .sk files can be saved with the JSON option.
    """
    # print(f'pio_args: {pio_args}')
    # pio = resolve_payload("out", **pio_args) # TODO direction?
    print(f'wallet: {wallet}')
    # return # TODO finish
    # sk_path = Path(sk_path)
    sk_json = asyncio.run(Client().wallet_save())
    w = Wallet.from_json(sk_json)
    print(f'w: {w}')
    # if sk_path.exists():
    #     raise Exception(f'sk_path exists: {sk_path}')
    # with sk_path.open('w') as f:
    #     f.write(sk_json) # already json; no dump needed
    # click.echo(f"Saved wallet → {sk_path}")
    multi_save(wallet, w, exist_ok=False)
