import click
from .utils import RoleAwareGroup, ints_arg

@click.group(cls=RoleAwareGroup)
def records() -> None:
    """Post batches of records.

    Posting only one record to the blockchain at a time is inefficient (and bad
    for privacy!), so by default any command that creates a record just adds it
    to the current batch. Then you use the commands here to list, drop, or post
    them together.

    In general you can batch anything that should be posted by the same node
    during the same phase of the election. (Edge cases TBD)
    """

@records.command(roles=['admin', 'guardian', 'device'])
def list():
    "Enumerate current records."
    raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
@ints_arg()
def post(ints):
    "Post current records."
    click.echo(ints)
    # TODO what happens when they don't fit in one tx?
    # TODO optional phase advance
    raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
@ints_arg()
def drop(ints):
    """Delete current records without posting.

    This is probably most useful when manually testing commands in the CLI.
    You might also want to discard records if they fail verification,
    but in that case you should raise an error too.
    """
    click.echo(ints)
    raise NotImplementedError
