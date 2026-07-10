import click

@click.group()
def spoiled() -> None:
    "Decrypt spoiled ballots."

@spoiled.command()
def announce_share():
    pass

@spoiled.command()
def combine_shares():
    pass

@spoiled.command()
def decrypt_by_nonce():
    pass
