import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def tally() -> None:
    "Decrypt the final election tally."

@tally.command(roles=['admin'])
def create():
    pass

@tally.command(roles=['admin'])
def announce():
    pass

@tally.command(roles=['guardian'])
def announce_share():
    pass

@tally.command(roles=['admin'])
def combine_shares():
    pass
