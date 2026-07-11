import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def verification() -> None:
    "Verify an election, or specific properties/records."

@verification.command()
def create():
    pass

@verification.command()
def announce():
    pass

@verification.command(name='await')
def await_():
    pass
