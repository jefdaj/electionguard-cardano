import click
from egc_app.cli.utils import RoleAwareGroup
from pathlib import Path

import cloup
from cloup import option, option_group
from cloup.constraints import (
    require_all, mutually_exclusive, If, RequireAtLeast, accept_none
)

# @cloup.command()
# @option_group(
#     "Inline ints",
#     option("--width", type=int),
#     option("--height", type=int),
#     constraint=require_all,          # if any given, both required
# )
# @option_group(
#     "Config file",
#     option("--config", type=cloup.file_path(exists=True)),
# )
# # exactly one of the two "sources" must be used
# @cloup.constraint(
#     mutually_exclusive & RequireAtLeast(1),
#     ["width", "config"],             # representative params from each source
# )
# def cli(width, height, config):
#     if config:
#         width, height = load_ints(config)
#     ...


@click.group(cls=RoleAwareGroup)
def ceremony() -> None:
    "Perform the guardian key ceremony."

@ceremony.command(roles=['admin'])
@cloup.option_group(
    "Inline ceremony config",
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
@cloup.option_group(
    "Ceremony config from file",
    cloup.option("--config-path", type=cloup.file_path(exists=True)), # TODO can this be a multi_load?
)
@cloup.constraint(
    mutually_exclusive & RequireAtLeast(1),
    ["guardian_count", "config_path"], # representative params from each source
)
def create(
    guardian_count: int,
    guardian_quorum: int,
    config_path: Path
):
    """Announce key ceremony parameters.
    This is provisional based on the electionguard_gui key_ceremony_service.py;
    I'm not sure whether it's the right approach yet.
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
