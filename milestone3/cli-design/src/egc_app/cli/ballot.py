import click

@click.group()
def ballot() -> None:
    pass

@ballot.command()
def create():
    pass

@ballot.command()
def submit():
    pass

@ballot.command()
def cast():
    pass

@ballot.command()
def spoil():
    pass
