import click

@click.group()
def channel() -> None:
    "Request, add, remove, or await channels."

@channel.command()
def request():
    pass

@channel.command()
def add():
    pass

@channel.command()
def remove():
    pass

@channel.command(name='await')
def await_():
    pass
