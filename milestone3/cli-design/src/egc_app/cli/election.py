import click
from egc_app.client import Client

@click.group()
def election() -> None:
	pass

# TODO compress down to one string with colons?
# TODO and define a qrcode format... qrcode:egc:election:policy_id:slot_no:hash?
#      (ask though)
@election.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--slot-no', type=click.INT)
@click.option('--block-header-hash', type=click.STRING)
def set(policy_id, slot_no, block_header_hash):
    """Set which election the server is following."""
    resp = asyncio.run(Client().set_election(policy_id, slot_no, block_header_hash))
    click.echo(resp)

@election.command()
@click.option('--filter', type=click.STRING, required=False)
def observe(filter: str|None = None):
    """Stream election events to the terminal."""
    async def _run():
        async for event in Client().stream_events(filter):
            click.echo(event)
    asyncio.run(_run())
