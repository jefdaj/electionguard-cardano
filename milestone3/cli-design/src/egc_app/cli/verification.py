import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def verification() -> None:
    "Verify all or part of an election."

@verification.command()
def create():
    pass

@verification.command()
def announce():
    pass

@verification.command(name='await')
def await_():
    pass
