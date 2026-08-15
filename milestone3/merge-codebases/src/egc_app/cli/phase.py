import click
import asyncio
from egc import *
from egc_app.cli.utils import RoleAwareGroup
from egc_app.client import Client
import logging


LOG = logging.getLogger(__name__)


@click.group(cls=RoleAwareGroup)
def phase() -> None:
    "Get, await or advance to an election phase."

# TODO `egc phase post` instead?
@phase.command(roles=['admin'])
@click.option('--phase', type=click.STRING, required=True)
def advance(phase: str):
    old = asyncio.run(Client().phase_get())
    new = EgcPhase[phase.upper()] # TODO anything more we should do to parse?
    guard_phase_transition(
        resolve_onchain_phase(old),
        resolve_onchain_phase(new)
    )
    asyncio.run(Client().phase_advance(new_phase=new))

@phase.command()
def get():
    phase_ = asyncio.run(Client().phase_get())
    LOG.debug(f'phase_: {phase_}')
    click.echo(phase_.name.lower())

@phase.command(name='await')
@click.option('--phase', type=click.STRING, required=True)
def await_(phase: str):
    phase_ = EgcPhase[phase.upper()]
    asyncio.run(Client().phase_await(phase=phase_))
