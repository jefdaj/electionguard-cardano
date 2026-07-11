import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def manifest() -> None:
    "Create and announce an election manifest."

@manifest.command(roles=['admin'])
def create():
    pass

@manifest.command(roles=['admin'])
def announce():
    pass
