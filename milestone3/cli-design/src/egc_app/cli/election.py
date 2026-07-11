import click
import asyncio
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def election() -> None:
    "Create, stream events from, or end an election."

# TODO compress down to one string with colons?
# TODO and define a qrcode format... qrcode:egc:election:policy_id:slot_no:hash?
#      (ask though)
@election.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--since-slot', type=click.INT)
@click.option('--since-block', type=click.STRING)
def subscribe(**sub_cfg_kwargs):
    "Set which election the node is following."
    asyncio.run(Client().election_subscribe(**sub_cfg_kwargs))

# TODO elaborate filter to take structured queries?
@election.command()
@click.option('--filter', type=click.STRING, required=False)
def events(filter: str|None = None):
    """Stream election events to the terminal."""
    async def _run():
        async for event in Client().election_events(filter):
            click.echo(event)
    asyncio.run(_run())

@election.command(roles=['funder'])
def init():
    "Create the election by minting an admin channel token."
    raise NotImplementedError

@election.command(roles=['admin'])
def end():
    "End the election by burning the admin channel token."
    raise NotImplementedError

@election.command()
def burntesttokens():
    """!REMOVE BEFORE PRODUCTION USE!

    Burns all tokens, ending the election suddenly.
    Anyone can call this, not just the admin or funder.
    It helps clean up after broken tests.
    """
    raise NotImplementedError
