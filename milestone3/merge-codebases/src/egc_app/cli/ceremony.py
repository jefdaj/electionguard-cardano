import click
from egc_app.cli.utils import RoleAwareGroup
from pathlib import Path
from egc_app.cli.utils import *
from electionguard import CeremonyDetails
from egc_app.client import Client


# TODO do we need a ceremony show/save option to get the settings from the server?

@click.group(cls=RoleAwareGroup)
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command(roles=['admin'])
@multi_load('ceremony', CeremonyDetails, ['json'])
def create(
    ceremony: CeremonyDetails,
):
    """Announce key ceremony details.
    This is provisional based on the electionguard_gui key_ceremony_service.py.
    I'm not sure whether it's the right approach yet.
    The json input is mainly for scripted testing; later there should be
    explicit inline options for each part of the config.
    """
    asyncio.run(Client().ceremony_create(ceremony=ceremony))
    # TODO any need to raise_for_status here?

    # The decoded type should already be CeremonyDetails now
    # details = CeremonyDetails(guardian_count, guardian_quorum)

@ceremony.command()
def show():
    """Print your current ceremony details as JSON.
    Use jq to access fields if needed.
    For example:
    MY_N_GUARDIANS=$(egc ceremony show | jq '.number_of_guardians' -r)
    """
    # TODO encode/decode schema?
    ceremony = asyncio.run(Client().ceremony_show())
    click.echo(json.dumps(ceremony))

@ceremony.command(roles=['guardian'])
def keygen():
    raise NotImplementedError

@ceremony.command(roles=['guardian'])
def announce_pubkey():
    raise NotImplementedError

@ceremony.command(roles=['guardian'])
def announce_backup():
    raise NotImplementedError

@ceremony.command(roles=['guardian'])
def confirm_backup():
    raise NotImplementedError
