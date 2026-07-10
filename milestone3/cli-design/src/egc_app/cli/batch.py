import click

@click.group()
def batch() -> None:
    pass

@batch.command()
def add():
    pass

@batch.command()
def status():
    pass

@batch.command()
def flush():
    pass
