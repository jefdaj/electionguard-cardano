import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def wallet() -> None:
    "Basic wallet management for elections."

@wallet.command()
def create():
    "Generate wallet."
    raise NotImplementedError

@wallet.command()
def show():
    "Show wallet, except the private key."
    raise NotImplementedError

@wallet.command()
def load():
    "Load wallet from (.sk, .addr) files."
    raise NotImplementedError

@wallet.command()
def save():
    "Save wallet to (.sk, .addr) files."
    raise NotImplementedError

@wallet.command()
def clear():
    "Clear wallet, leaving files."
    raise NotImplementedError
