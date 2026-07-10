import click

@click.group()
def batch() -> None:
    "Batch multiple records into a transaction."

@batch.command()
def add():
    pass

@batch.command()
def status():
    pass

@batch.command()
def flush():
    pass
