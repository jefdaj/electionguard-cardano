import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def channel() -> None:
    "Request, add, remove, or await channels."

@channel.command()
def request():
    pass

@channel.command(roles=['admin'])
def add():
    pass

@channel.command(roles=['admin'])
def remove():
    pass

@channel.command(name='await')
def await_():
    pass
