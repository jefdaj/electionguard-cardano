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

def verify_from_public_record(pubdir, errors, artifact_name, msg, **fmtargs):
    "Wrap from_public_record with verification stuff"
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
# list of already-verified dependency nodes `vdeps` and optional extra `kwargs`
# (for example `ballot_id`). It returns whether verification succeeded.
#
# TODO is throwing an exception also OK, or should it be cast to str?
# TODO should kwargs be passed expanded instead?
#
#############################################

def verify_manifest(pubdir, errors, vdeps, kwargs={}) -> bool:
    msg = 'manifest'
    return verify_from_public_record(pubdir, errors, 'manifest', msg)

def verify_ceremony_details(pubdir, errors, vdeps, kwargs={}) -> bool:
    msg = 'ceremony_details'
    return verify_from_public_record(pubdir, errors, 'ceremony_details', msg)

def verify_guardian_pubkey(pubdir, errors, vdeps, guardian_id) -> bool:
    msg = f'{guardian_id}'
    return verify_from_public_record(
        pubdir, errors, 'guardian_pubkey', msg,
        guardian_id=guardian_id
    )

# TODO are these verified at all? they aren't public in the spec
def verify_guardian_backup(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

# TODO are these verified at all? they aren't public in the spec
def verify_guardian_verification(pubdir, errors, vdeps, kwargs={}) -> bool:
    return "not implemented yet"

def verify_joint_key(pubdir, errors, vdeps, kwargs={}) -> bool:
    msg = 'joint_key'
    return verify_from_public_record(pubdir, errors, 'joint_key', msg)

# TODO is this ever used?
def verify_constants(pubdir, errors, vdeps, kwargs={}) -> bool:
    msg = 'constants'
    return verify_from_public_record(pubdir, errors, 'constants', msg)

def verify_context(pubdir, errors, vdeps, kwargs={}) -> bool:
    msg = 'constants'
    return verify_from_public_record(pubdir, errors, 'context', msg)

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
    ceremony_details = vdeps['ceremony_details']
    guardian_pubkeys: Dict[GuardianId, ElectionPublicKey] = {}
    print('\nguardian pubkeys:')
    for n in range(1, ceremony_details.number_of_guardians+1):
        guardian_id = f'guardian_{n}'
        pubkey = verify_guardian_pubkey(
            pubdir, errors, {},
            guardian_id=guardian_id
        )
        if pubkey is not None:
            guardian_pubkeys[guardian_id] = pubkey
    return guardian_pubkeys

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
    print('verifying public election artifacts...\n')
    verify_manifest(pubdir, errors, {}, {})
    ceremony_details = verify_ceremony_details(pubdir, errors, {}, {})
    vdeps = {'ceremony_details': ceremony_details}
    verify_all_guardian_pubkeys(pubdir, errors, vdeps, {})


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
