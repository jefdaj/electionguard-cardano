import asyncio
import click
from .utils import RoleAwareGroup, indexes_arg
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
    This gives indexes for use in the post and drop commands.
    """
    # TODO and estimates how many will fit in a tx?
    data = asyncio.run(Client().records_list())
    print('index\tmetadata')
    for (index, metadata) in enumerate(data.records, start=1):
        print(f'{index}\t{metadata}')

@records.command(roles=['admin', 'guardian', 'device'])
@click.option('--min-size', help='Min batch size for privacy.', type=click.INT, required=False)
@click.option('--advance-phase', help='Admin only: also advance the election phase.', type=click.STRING, required=False)
@indexes_arg(required=False)
def post(indexes: list[int], min_size: int, advance_phase: str):
    """Post current records.
    You can optionally specify indexes/ranges.
    By default it posts as many as fit in a single transaction, starting from index 1.
    The advance phase option is only applied if you're the admin and all records fit.

    Min size is a basic placeholder for privacy settings; future versions
    should have more robust options to allow tuning batches based on number of
    voters expected to use a machine, number of variations in the ballot, how
    long voters are prepared to wait to challenge their submitted ballots, etc.
    """
    # TODO return code to indicate whether all records fit or not? or print something? or use list?
    click.echo(indexes)
    # TODO parse phase
    asyncio.run(Client().records_post(
        indexes,
        min_size      = min_size,
        advance_phase = advance_phase
    ))
    raise NotImplementedError


@records.command(roles=['admin', 'guardian', 'device'])
@indexes_arg(required=True)
def drop(indexes: list[int]):
    """Delete current records without posting.
    Mainly for testing.
    Requires explicit indexes/ranges.
    """
    asyncio.run(Client().records_drop(indexes))
