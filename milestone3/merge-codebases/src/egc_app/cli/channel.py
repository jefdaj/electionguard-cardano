import click
from egc_app.cli.utils import RoleAwareGroup
from egc_app import schemas

@click.group(cls=RoleAwareGroup)
def channel() -> None:
    "Request, add, remove, or await channels."

@click.option('--role', type=click.STRING, required=True)
@channel.command(roles=['observer'])
def request(role: str):
    """Save a subchannel request.

    Subchannel requests are communicated to the admin offchain.
    This saves your request to JSON or a QR code.
    """
    # TODO guard wallet
    # TODO guard role
    # TODO guard election? maybe not needed
    raise NotImplementedError

@channel.command(roles=['admin'])
def add():
    "Add (mint) a subchannel."
    raise NotImplementedError

@channel.command(roles=['admin'])
def remove():
    "Remove (burn) a subchannel."
    raise NotImplementedError

@channel.command(name='await')
@click.option('--role', type=click.STRING, required=True)
def await_(role: str):
    """Wait for your channel to appear.

    This should normally be done by an observer. You can also use it once you
    have a role, but then it's more like an assert statement. The admin can
    also use this to wait for their channel from the funder.
    """
    asyncio.run(Client().channel_await(role=role))
