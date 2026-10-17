import asyncio
import click
from typing import Optional
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
    asyncio.run(Client().collateral_await())

@collateral.command(name='return') # TODO roles?
@click.option('--return-addr', type=click.STRING, required=False)
def return_(return_addr: Optional[str]):
    asyncio.run(Client().collateral_return(return_addr=return_addr))
