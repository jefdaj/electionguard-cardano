import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def batch() -> None:
    "Batch multiple records into a transaction."

# TODO verifier? could batch but have no reason to
@batch.command(roles=['admin', 'guardian', 'device'])
def add():
    raise NotImplementedError

@batch.command(roles=['admin', 'guardian', 'device'])
def status():
    raise NotImplementedError

@batch.command(roles=['admin', 'guardian', 'device'])
def flush():
    raise NotImplementedError
