import click
from .utils import RoleAwareGroup, ints_arg

@click.group(cls=RoleAwareGroup)
def records() -> None:
    """Post batches of records.

    Posting only one record to the blockchain at a time is inefficient--and bad
    for privacy! So any command that creates a record adds it to the current
    batch instead. Then you use the commands here to list, drop, or post them
    as a group.

    In general you can batch anything that should be posted by the same node
    during the same phase of the election; edge cases TBD.
    """

@records.command(name='list', roles=['admin', 'guardian', 'device'])
def list_():
    """Enumerate current records.
    This gives indices for use in the post and drop commands.
    """
    # TODO and estimates how many will fit in a tx?
    raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
@ints_arg()
def post(ints):
    """Post current records.
    Defaults to all records, but you can optionally specify them by number.
    The admin can also optionally advance the phase at the same time.
    """
    click.echo(ints)
    # TODO what happens when they don't fit in one tx?
    # TODO optional phase advance
    raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
@ints_arg(required=True)
def drop(ints):
    """Delete current records without posting.
    Requires explicit indices for which ones to drop.

    This is probably most useful when manually testing commands in the CLI.
    You might also want to discard records if they fail verification,
    but in that case you should raise an error too.
    """
    click.echo(ints)
    raise NotImplementedError
