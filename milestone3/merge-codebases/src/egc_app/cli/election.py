import click
import cloup
from cloup.constraints import RequireExactly
import asyncio
from egc import ElectionConfig, scan_qrcode, print_qrcode # TODO relative?
from egc_app.client import Client
from egc_app.cli.utils import *
from egc import *

@click.group(cls=RoleAwareGroup)
def election() -> None:
    "Create, share, stream, or end an election."

@election.command()
@multi_load("election", ElectionConfig, ["cam", "png", "txt", "json"])
def subscribe(election: ElectionConfig):
    "Set which election the node is following."
    # TODO should this reset a non-observer node back to observer?
    asyncio.run(Client().election_subscribe(election))

# TODO rename -> share?
# TODO option to share json instead?
@election.command()
@click.pass_context
def qrcode(ctx):
    "Share subscribe config as a QR code."
    # TODO what should the error be if no election config yet?
    election = ctx.find_root().default_map.get("election")
    config = ElectionConfig.from_dict(election)
    print_qrcode(config)

# TODO error if ogmios unreachable? or separate status endpoint expected for that?
# TODO elaborate filter to take structured queries?
@election.command()
@cloup.option('--filter', type=click.STRING, required=False)
def events(filter: str|None = None):
    """Stream election events to the terminal."""
    # TODO we also want errors to come through on this channel, so should they be events?
    async def _run():
        async for e in Client().election_events(filter):
            msg = f'{e.slot_no} {e.channel} {e.event_desc}'
            click.echo(msg)
    asyncio.run(_run())

# The reason this is for an observer is that you don't want to run it while
# having an official role in another election. And you start as an observer.
# TODO accept a qrcode (file or scan) as the admin addr
# TODO accept a qrcode (file or scan) as the funder sk
@election.command(roles=['observer'])
@multi_load("funder", Wallet, ["json"])
def init(funder: Wallet):
    """Create an election by minting an admin channel token.

    There are two main ways you might want to do this. Note that
    only method 1a is implemented in the demo/mvp version, because
    it makes it easier to test with a single dev wallet:

    1. If you're the admin and also the funder, you should generate your
    admin wallet first. Then you can either:

    \b
    a. pass a separate funder wallet (sk path) here
    b. fund the admin wallet from the faucet before continuing

    Either way, you'll become the admin. Example:

    \b
      egc wallet create --name admin
      egc election init --funder-load-json ./wallets/funder.sk
      egc channel await --role admin

    2. If you're the funder but not the admin, load your wallet and then run
    this, passing a separate admin addr. You'll become an observer.
    Example:

    \b
      egc wallet load --wallet-load-json ./wallets/funder.sk
      egc election init --admin-load-json ./wallets/admin.addr
      egc election events

    Either way, this command will clear any previous election state and
    subscribe to the new election.
    """
    click.echo(funder)

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
