import click

@click.group()
def phase() -> None:
    pass

@phase.command()
def announce():
    pass

@phase.command(name='await')
def await_():
    pass
