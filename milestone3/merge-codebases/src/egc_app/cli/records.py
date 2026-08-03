import click
# from egc_app.cli.utils import RoleAwareGroup, ints_arg
from .utils import RoleAwareGroup, ints_arg

@click.group(cls=RoleAwareGroup)
def records() -> None:
    "Control batching of records into transactions."

@records.command(roles=['admin', 'guardian', 'device'])
def list():
    "Enumerate the current records."
    raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
@ints_arg()
def post(ints):
    "Post the current records."
    click.echo(ints)
    # TODO what happens when they don't fit in one tx?
    # TODO optional phase advance
    # raise NotImplementedError

@records.command(roles=['admin', 'guardian', 'device'])
def drop():
    """Drop current records without posting.

    This is probably most useful when manually testing commands in the CLI.
    You might also want to discard records if they fail verification,
    but in that case you should raise an error too.
    """
    raise NotImplementedError
