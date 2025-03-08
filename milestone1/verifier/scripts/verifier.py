#!/usr/bin/env python3

import click
from collections import defaultdict
from utils import (
    # build_election,
    # load_submitted_ballots,
    # load_cast_ballots,
    # load_tally_shares,
    # load_spoiled_shares,
    # load_spoiled_results,
    # load_guardian_pubkeys_dict,
    # load_spoiled_ballots,
    # to_public_record,
    from_public_record,
)


### utils ###

def verify_from_public_record(pubdir, errors, artifact_name, **fmtargs):
    "Wrap from_public_record with verification stuff"
    msg = f'loading {artifact_name} and checking its format'
    try:
        artifact = from_public_record(pubdir, artifact_name, **fmtargs)
        print(f'✅ {msg}')
        return artifact
    except Exception as e:
        errors[artifact_name] = str(e)
        print(f'❌ {msg}')
        print(errors)


### verify a node in the dependency graph ###
#
# Each function takes the main public dir `pubdir`, the main `errors` dict, a
# list of alreadfy-verified dependency nodes `vdeps` and optional extra
# `kwargs`. It returns whether verification succeeded.
#
# TODO is throwing an exception also OK, or should it be cast to str?
# TODO should kwargs be passed expanded instead?
#
#############################################

def verify_manifest(pubdir, errors, vdeps, kwargs={}) -> bool:
    verify_from_public_record(pubdir, errors, 'manifest')

def verify_ceremony_details(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_guardian_pubkey(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_guardian_backup(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_guardian_verification(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_joint_key(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_constants(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_context(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_device(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ballot_submitted(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_cast_notice(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ballot_spoiled(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ciphertext_tally(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_tally_share(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_spoiled_share(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_plaintext_tally(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_spoiled_result(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_guardian_pubkeys(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_ballots_submitted(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_ballots_spoiled(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_cast_notices(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_ballots(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_spoiled_shares(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_spoiled_results(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_tally_shares(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_build_election(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_internal_manifest(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_election(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_summary(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"


### main ###

def main(pubdir, verifier_id):
    errors = defaultdict(lambda: {})
    print('verifying public election artifacts...')
    verify_manifest(pubdir, errors, {}, {})


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
