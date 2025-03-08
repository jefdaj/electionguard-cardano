#!/usr/bin/env python3

import click
from typing import Optional


### utils ###

def verify_from_public_record(public_dir, artifact_name, **kwargs):
    "Wrap from_public_record with verification stuff"


### verify a node in the dependency graph ###
#
# Each function returns None for success, or a str explaining the error.
# It takes a list of dependency nodes `deps` and optional extra `kwargs`.
#
# TODO is throwing an exception also OK, or should it be cast to str?
# TODO should kwargs be passed expanded instead?
#
#############################################

def verify_manifest(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_ceremony_details(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_guardian_pubkey(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_guardian_backup(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_guardian_verification(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_joint_key(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_constants(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_context(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_device(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_ballot_submitted(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_cast_notice(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_ballot_spoiled(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_ciphertext_tally(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_tally_share(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_spoiled_share(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_plaintext_tally(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_spoiled_result(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_guardian_pubkeys(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_ballots_submitted(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_ballots_spoiled(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_cast_notices(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_ballots(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_spoiled_shares(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_spoiled_results(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_all_tally_shares(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_build_election(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_internal_manifest(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_election(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"

def verify_summary(public_dir, deps, kwargs={}) -> Optional[str]:
    return "not implemented yet"


### main ###

def main(public_dir, verifier_id):
    pass


### cli ###

@click.command("verify")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--verifier-id",
    prompt="Unique ID for this verifier",
    help="Used when saving the final JSON summary file",
    type=click.STRING,
)
def VerifyCommand(
    public_dir: str,
    verifier_id: str,
) -> None:
    """Verify all public election artifacts.
    """
    # TODO parse and pass cfg here
    main(public_dir, verifier_id)

@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()
