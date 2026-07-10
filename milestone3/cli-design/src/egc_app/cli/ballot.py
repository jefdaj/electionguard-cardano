import click

@click.group()
def ballot() -> None:
    "Create, submit, and cast/spoil ballots."

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
