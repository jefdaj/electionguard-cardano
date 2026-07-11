import click
import asyncio
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def election() -> None:
    "Create, observe, or end an election."

# TODO compress down to one string with colons?
# TODO and define a qrcode format... qrcode:egc:election:policy_id:slot_no:hash?
#      (ask though)
@election.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--slot-no', type=click.INT)
@click.option('--block-header-hash', type=click.STRING)
def subscribe(policy_id, slot_no, block_header_hash):
    "Set which election the node is following."
    resp = asyncio.run(Client().election_subscribe(policy_id, slot_no, block_header_hash))
    click.echo(resp)

@election.command()
@click.option('--filter', type=click.STRING, required=False)
def observe(filter: str|None = None):
    """Stream election events to the terminal."""
    async def _run():
        async for event in Client().election_events(filter):
            click.echo(event)
    asyncio.run(_run())

@election.command(roles=['admin']) # TODO funder?
def init():
    "Create the election by minting an admin channel token."

@election.command(roles=['admin'])
def end():
    "End the election by burning the admin channel token."

@election.command()
def burntesttokens():
    "!REMOVE BEFORE PRODUCTION USE!"
