import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def ballot() -> None:
    "Create, submit, and cast/spoil ballots."

@ballot.command(roles=['device'])
def create():
    pass

@ballot.command(roles=['device'])
def submit():
    pass

@ballot.command(roles=['device'])
def cast():
    pass

@ballot.command(roles=['device'])
def spoil():
    pass
