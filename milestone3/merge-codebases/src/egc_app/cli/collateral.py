import asyncio
import click
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def collateral() -> None:
    "Create, await, or return collateral."

@collateral.command() # TODO roles?
def create():
    raise NotImplementedError

@collateral.command(name='await') # TODO roles?
def await_():
    raise NotImplementedError

@collateral.command(name='return') # TODO roles?
def return_():
    asyncio.run(Client().collateral_return())
