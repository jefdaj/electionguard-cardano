import click
from egc_app.cli.utils import RoleAwareGroup
from pathlib import Path
from egc_app.cli.utils import *
from electionguard import CeremonyDetails


@click.group(cls=RoleAwareGroup)
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command(roles=['admin'])
@multi_load('ceremony', CeremonyDetails, ['json'])
def create(
    ceremony: CeremonyDetails,
):
    """Announce key ceremony parameters.
    This is provisional based on the electionguard_gui key_ceremony_service.py.
    I'm not sure whether it's the right approach yet.
    The json input is mainly for scripted testing; later there should be
    explicit inline options for each part of the config.
    """
    # raise NotImplementedError
    print(locals())
    return

    # The decoded type should already be CeremonyDetails now
    # details = CeremonyDetails(guardian_count, guardian_quorum)

    # TODO just have to save in the proper spot?
    # TODO convert back to json, send -> server, then it does this:
    # to_public_record(egsync_api, 'admin_1', 'ceremony_details', details)


# TODO remove unless different from create
# @ceremony.command(roles=['admin'])
# def announce():
#     raise NotImplementedError

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
