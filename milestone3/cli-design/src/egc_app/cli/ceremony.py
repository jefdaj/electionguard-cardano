import click

@click.group()
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command()
def create():
    pass

@ceremony.command()
def announce():
    pass

@ceremony.command()
def keygen():
    pass

@ceremony.command()
def announce_pubkey():
    pass

@ceremony.command()
def announce_backup():
    pass

@ceremony.command()
def confirm_backup():
    pass
