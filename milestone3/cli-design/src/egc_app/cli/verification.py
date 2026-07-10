import click

@click.group()
def verification() -> None:
    "Verify an election, or specific properties/records."

@verification.command()
def create():
    pass

@verification.command()
def announce():
    pass

@verification.command(name='await')
def await_():
    pass
