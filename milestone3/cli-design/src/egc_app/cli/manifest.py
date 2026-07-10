import click

@click.group()
def manifest() -> None:
    pass

@manifest.command()
def create():
    pass

@manifest.command()
def announce():
    pass
