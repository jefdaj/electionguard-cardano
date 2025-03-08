#!/usr/bin/env python3

import click
from typing import Any, Union, Optional
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
import pygraphviz as pgv
from dataclasses import dataclass, field


### utils ###

def mark_failed(results, artifact_name, error_msg):
    results[artifact_name].attempted = True
    results[artifact_name].result = error_msg

def mark_verified(results, artifact_name, obj):
    results[artifact_name].attempted = True
    results[artifact_name].result = obj

def verify_from_public_record(pubdir, results, artifact_name, msg=None, **fmtargs):
    "Wrap from_public_record with verification stuff"
    if msg is None:
        msg = artifact_name
    try:
        artifact = from_public_record(pubdir, artifact_name, **fmtargs)
        mark_verified(results, artifact_name, artifact)
        print(f'✅ {msg}')
        # TODO is returning it redundant?
        return artifact
    except Exception as e:
        mark_failed(results, artifact_name, str(e))
        print(f'❌ {msg}')

@dataclass
class VerifyState:

    verify_fn: Callable[str, dict, dict] = field(init=False)

    # whether we've already tried to verify this one
    attempted: bool = field(init=True, default=False)

    # str means error msg; anything else is success
    # TODO is this optional union thing really the best way?
    result: Optional[Union[str, Any]] = field(init=True, default=None)


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

def verify_manifest(results, pubdir, kwargs={}) -> bool:
    return verify_from_public_record(pubdir, results, 'manifest')

def verify_ceremony_details(results, pubdir, kwargs={}) -> bool:
    return verify_from_public_record(pubdir, results, 'ceremony_details')

def verify_guardian_pubkey(results, pubdir, guardian_id) -> bool:
    msg = f'{guardian_id}'
    return verify_from_public_record(
        pubdir, errors, 'guardian_pubkey', msg,
        guardian_id=guardian_id
    )

# TODO are these verified at all? they aren't public in the spec
def verify_guardian_backup(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

# TODO are these verified at all? they aren't public in the spec
def verify_guardian_verification(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_joint_key(results, pubdir, kwargs={}) -> bool:
    return verify_from_public_record(pubdir, results, 'joint_key')

# TODO is this ever used?
def verify_constants(results, pubdir, kwargs={}) -> bool:
    return verify_from_public_record(pubdir, results, 'constants')

def verify_context(results, pubdir, kwargs={}) -> bool:
    return verify_from_public_record(pubdir, results, 'context')

def verify_device(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ballot_submitted(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_cast_notice(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ballot_spoiled(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_ciphertext_tally(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_tally_share(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_spoiled_share(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_plaintext_tally(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_spoiled_result(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_guardian_pubkeys(results, pubdir, kwargs={}) -> bool:
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

def verify_all_ballots_submitted(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_ballots_spoiled(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_cast_notices(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_ballots(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_spoiled_shares(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_spoiled_results(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_all_tally_shares(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_build_election(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_internal_manifest(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_election(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"

def verify_summary(results, pubdir, kwargs={}) -> bool:
    return "not implemented yet"


### main ###

def list_deps(depgraph, artifact_name):
    return depgraph.predecessors(artifact_name)

def verify_artifact(depgraph, results, pubdir, artifact_name):
    dep_names = list_deps(depgraph, artifact_name)
    vdeps = {}
    for dep_name in dep_names:
        verify_fn = globals()[f'verify_{dep_name}']
        try:
            vdeps[dep_name] = verify_artifact(depgraph, results, pubdir, dep_name)
        except Exception as e:
            errors[dep_name] = str(e)
            return

def main(pubdir, verifier_id):

    # describes dependencies, and can be rendered to debug
    depgraph = pgv.AGraph('/scripts/verifier_deps.dot')

    # main state is a dict of artifact_name -> VerifyState
    # it accumulates both successful result objects and error messages
    exclude_fns = ['verify_from_public_record', 'verify_artifact']
    results = {
        name.replace('verify_', ''): VerifyState(fn)
        for (name,fn) in globals().items()
        if name.startswith('verify_') and not name in exclude_fns
    }
    # print(results)

    print('verifying public election artifacts...\n')

    # verify_manifest(pubdir, results, {}, {})
    # ceremony_details = verify_ceremony_details(pubdir, results, {}, {})
    # vdeps = {'ceremony_details': ceremony_details}
    # verify_all_guardian_pubkeys(results, pubdir, {})


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
