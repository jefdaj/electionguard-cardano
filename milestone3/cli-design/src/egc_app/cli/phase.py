import click

@click.group()
def phase() -> None:
    "Announce or await a particular election phase."

@phase.command()
def announce():
    pass

@phase.command(name='await')
def await_():
    pass
