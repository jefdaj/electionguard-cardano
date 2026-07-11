import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def phase() -> None:
    "Announce or await an election phase."

@phase.command(roles=['admin'])
def announce():
    pass

@phase.command(name='await')
def await_():
    pass
