import click
import cloup
from cloup.constraints import RequireExactly
import asyncio
from egc import SubscriberConfig, scan_qrcode, print_qrcode # TODO relative?
from egc_app.client import Client
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def election() -> None:
    "Create, share, stream, or end an election."

# TODO clean up and factor out the qrcode parts
@election.command()
@cloup.option_group(
    "Election input options",
    cloup.option('--scan-qrcode', is_flag=True, required=False),
    cloup.option('--parse-str', type=click.STRING, required=False),
    RequireExactly(1),
)
def subscribe(**kwargs):
    """Set which election the node is following.

    For --parse-str, the input should be in the same format
    you would get from the QR code. Line wraps are OK.

    egc:election:<policy_id>:<since_slot>:<since_block>
    """
    # print(f'sub_cfg_kwargs: {sub_cfg_kwargs}')
    # print(f'kwargs: {kwargs}')
    if kwargs['scan_qrcode']:
        sub_cfg = scan_qrcode(decode_cls=SubscriberConfig)
    else:
        sub_cfg = SubscriberConfig.from_qr_str(kwargs['parse_str'])
    asyncio.run(Client().election_subscribe(sub_cfg))

# TODO rename -> share?
# TODO option to share json instead?
@election.command()
@click.pass_context
def qrcode(ctx):
    "Share subscribe config as a QR code."
    # TODO what should the error be if no election config yet?
    election = ctx.find_root().default_map.get("election")
    sub_cfg = SubscriberConfig.from_dict(election['subscribe'])
    print_qrcode(sub_cfg)

# TODO error if ogmios unreachable? or separate status endpoint expected for that?
# TODO elaborate filter to take structured queries?
@election.command()
@cloup.option('--filter', type=click.STRING, required=False)
def events(filter: str|None = None):
    """Stream election events to the terminal."""
    async def _run():
        async for event in Client().election_events(filter):
            click.echo(event)
    asyncio.run(_run())

# The reason this is for an observer is that you don't want to run it while
# having an official role in another election. And you start as an observer.
# TODO accept a qrcode (file or scan) as the admin addr
# TODO accept a qrcode (file or scan) as the funder sk
@election.command(roles=['observer'])
@cloup.option('--funds-from', type=click.STRING, required=False)
@cloup.option('--admin-addr', type=click.STRING, required=False)
def init():
    """Create an election by minting an admin channel token.

    There are two main ways you might want to do this:

    1. If you're the funder but not the admin, load your wallet and then run
    this, passing a separate admin addr. You'll become an observer.
    Example:

    \b
      egc wallet load ./keys/funder.sk
      egc election init --admin-addr ./keys/admin.addr
      egc election events

    2. If you're the admin and also sending funds, you should generate your
    admin wallet first. Then you can either fund that wallet from the faucet
    (https://docs.cardano.org/cardano-testnets/tools/faucet), or pass a
    separate funder wallet sk here. You'll become the admin. Example:

    \b
      egc wallet create
      egc election init [--funds-from ./keys/funder.sk]
      egc channel await --role 'admin'

    Either way, this command will clear any previous election state and
    subscribe to the new election.
    """
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
