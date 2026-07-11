import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def batch() -> None:
    "Batch multiple records into a transaction."

# TODO verifier? could batch but have no reason to
@batch.command(roles=['admin', 'guardian', 'device'])
def add():
    pass

@batch.command(roles=['admin', 'guardian', 'device'])
def status():
    pass

@batch.command(roles=['admin', 'guardian', 'device'])
def flush():
    pass
