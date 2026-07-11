import click
from egc_app.cli.utils import RoleAwareGroup

@click.group(cls=RoleAwareGroup)
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command(roles=['admin'])
def create():
    pass

@ceremony.command(roles=['admin'])
def announce():
    pass

@ceremony.command(roles=['guardian'])
def keygen():
    pass

@ceremony.command(roles=['guardian'])
def announce_pubkey():
    pass

@ceremony.command(roles=['guardian'])
def announce_backup():
    pass

@ceremony.command(roles=['guardian'])
def confirm_backup():
    pass
