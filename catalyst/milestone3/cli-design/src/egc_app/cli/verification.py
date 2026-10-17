import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def verification() -> None:
    "Verify all or part of an election."

@verification.command()
def create():
    raise NotImplementedError

# TODO also device?
@verification.command(roles=['admin', 'guardian', 'verifier'])
def announce():
    raise NotImplementedError

@verification.command(name='await')
def await_():
    raise NotImplementedError
