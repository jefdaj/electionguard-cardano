import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the current EGC node config."

@config.command()
def node():
    pass

@config.command()
def election():
    pass

@config.command()
def batch():
    pass
