import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def tally() -> None:
    "Decrypt the final election tally."

@tally.command(roles=['admin'])
def create():
    raise NotImplementedError

@tally.command(roles=['admin'])
def announce():
    raise NotImplementedError

@tally.command(roles=['guardian'])
def announce_share():
    raise NotImplementedError

@tally.command(roles=['admin'])
def combine_shares():
    raise NotImplementedError
