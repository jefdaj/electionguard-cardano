import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def batch() -> None:
    "Batch multiple records into a transaction."

# TODO verifier? could batch but have no reason to
@batch.command(roles=['admin', 'guardian', 'device'])
def add():
    "Add a record to the current batch."
    raise NotImplementedError

@batch.command(roles=['admin', 'guardian', 'device'])
def status():
    "Inspect the current batch."
    raise NotImplementedError

@batch.command(roles=['admin', 'guardian', 'device'])
def publish():
    "Publish the current batch."
    raise NotImplementedError

@batch.command(roles=['admin', 'guardian', 'device'])
def discard():
    """Drop the current batch without publishing.

    This is probably most useful when manually testing commands in the CLI.
    You might also want to discard records if they fail verification,
    but in that case you should raise an error too.
    """
    raise NotImplementedError
