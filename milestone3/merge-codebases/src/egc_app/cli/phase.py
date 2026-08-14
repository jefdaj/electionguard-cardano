import click
import asyncio
from egc import *
from egc_app.cli.utils import RoleAwareGroup
from egc_app.client import Client

@click.group(cls=RoleAwareGroup)
def phase() -> None:
    "Get, await or advance to an election phase."

# TODO `egc phase post` instead?
@phase.command(roles=['admin'])
@click.option('--phase', type=click.STRING, required=True)
def advance(phase: str):
    phase = EgcPhase[phase.upper()] # TODO anything more we should do to parse?
    asyncio.run(Client().phase_advance(phase=phase))

@phase.command()
def get():
    phase = asyncio.run(Client().phase_get())
    print(f'phase: {phase}')
    print(f'phase type: {type(phase)}')
    click.echo(phase)

@phase.command(name='await')
@click.option('--phase', type=click.STRING, required=True)
def await_(phase: str):
    phase = EgcPhase[phase.upper()] # TODO anything more we should do to parse?
    asyncio.run(Client().phase_await(phase=phase))
