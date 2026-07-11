import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def batch() -> None:
    "Batch multiple records into a transaction."

@batch.command()
def add():
    pass

@batch.command()
def status():
    pass

@batch.command()
def flush():
    pass
