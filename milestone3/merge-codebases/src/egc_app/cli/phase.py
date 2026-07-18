import click
import asyncio
from egc_app.cli.utils import RoleAwareGroup
from egc_app.client import Client

@click.group(cls=RoleAwareGroup)
def phase() -> None:
    "Announce or await an election phase."

@phase.command(roles=['admin'])
def announce():
    raise NotImplementedError

@phase.command()
def get():
    phase = asyncio.run(Client().phase_get())
    print(f'phase: {phase}')
    print(f'phase type: {type(phase)}')
    click.echo(phase)

@phase.command(name='await')
def await_():
    raise NotImplementedError
