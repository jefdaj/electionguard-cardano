import click

@click.group()
def manifest() -> None:
    "Create and announce an election manifest."

@manifest.command()
def create():
    pass

@manifest.command()
def announce():
    pass
