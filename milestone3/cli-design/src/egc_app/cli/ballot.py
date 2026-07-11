import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def ballot() -> None:
    "Create, submit, and cast/spoil ballots."

@ballot.command(roles=['device'])
def create():
    raise NotImplementedError

@ballot.command(roles=['device'])
def submit():
    raise NotImplementedError

@ballot.command(roles=['device'])
def cast():
    raise NotImplementedError

@ballot.command(roles=['device'])
def spoil():
    raise NotImplementedError
