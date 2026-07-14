import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def channel() -> None:
    "Request, add, remove, or await channels."

@channel.command(roles=['admin', 'guardian', 'device', 'verifier'])
def request():
    """Save a subchannel request.

    Subchannel requests are communicated to the admin offchain.
    This saves your request to JSON or a QR code.
    """
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
def await_():
    """Wait for your channel to appear.

    This should normally be done by an observer. You can also use it once you
    have a role, but then it's more like an assert statement. The admin can
    also use this to wait for their channel from the funder.
    """
    raise NotImplementedError
