import click
from egc_app.cli.utils import RoleAwareGroup
from pathlib import Path
from egc_app.cli.utils import *

import cloup
from cloup import option, option_group
from cloup.constraints import (
    require_all, mutually_exclusive, If, RequireAtLeast, accept_none
)


@click.group(cls=RoleAwareGroup)
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command(roles=['admin'])
@cloup.option_group(
    "Inline ceremony input",
    cloup.option(
        "--guardian-count",
        prompt="Number of guardians",
        help="The number of guardians that will participate in the key ceremony and tally.",
        type=click.INT,
    ),
    cloup.option(
        "--guardian-quorum",
        prompt="Quorum",
        help="The minimum number of guardians required to show up to the tally.",
        type=click.INT,
    ),
    constraint = require_all,
)
@multi_load("ceremony", dict, ["json"])
@cloup.constraint(
    mutually_exclusive & RequireAtLeast(1),
    ["guardian_count", "ceremony_load_json"], # representative params from each source
)
def create(
    guardian_count: int,
    guardian_quorum: int,
    config_path: Path
):
    """Announce key ceremony parameters.
    This is provisional based on the electionguard_gui key_ceremony_service.py;
    I'm not sure whether it's the right approach yet.

    You can either set all the options inline, or load them all from a JSON config file.
    """
    # raise NotImplementedError
    print(locals())
    return

    details = CeremonyDetails(guardian_count, guardian_quorum)
    to_public_record(egsync_api, 'admin_1', 'ceremony_details', details)


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
