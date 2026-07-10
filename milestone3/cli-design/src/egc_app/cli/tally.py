import click

@click.group()
def tally() -> None:
    "Decrypt the final election tally."

@tally.command()
def create():
    pass

@tally.command()
def announce():
    pass

@tally.command()
def announce_share():
    pass

@tally.command()
def combine_shares():
    pass
