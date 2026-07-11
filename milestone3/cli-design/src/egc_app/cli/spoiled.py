import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def spoiled() -> None:
    "Decrypt spoiled ballots."

@spoiled.command(roles=['guardian'])
def announce_share():
    raise NotImplementedError

@spoiled.command(roles=['admin'])
def combine_shares():
    raise NotImplementedError

@spoiled.command(roles=['verifier', 'observer'])
def decrypt_by_nonce():
    raise NotImplementedError
