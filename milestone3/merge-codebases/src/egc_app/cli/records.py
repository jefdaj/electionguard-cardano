import asyncio
import click
from .utils import RoleAwareGroup, ints_arg
from egc_app.client import Client

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
    data = asyncio.run(Client().records_list())
    print('index\tmetadata')
    for (index, metadata) in enumerate(data.records, start=1):
        print(f'{index}\t{metadata}')

@records.command(roles=['admin', 'guardian', 'device'])
@click.option('--min-size', help='Min batch size for privacy.', type=click.INT, required=False)
@click.option('--advance-phase', help='Admin only: also advance the election phase.', type=click.STRING, required=False)
@ints_arg()
def post(ints: list[int], min_size: int, advance_phase: str):
    """Post current records.
    Defaults to as many as will fit in one transaction, but you can optionally
    specify indices.
    """
    click.echo(ints)
    # TODO what happens when they don't fit in one tx?
    # TODO parse phase
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
