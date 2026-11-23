from .types import *
import logging

from typing import Union

# TODO unify this with current core.records code
from .utils import from_public_record

from electionguard.election import CiphertextElectionContext
from electionguard.guardian import GuardianId
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.tally import PlaintextTally

# from electionguard_verify import *


# from https://stackoverflow.com/a/2704866
def freeze_kwargs(kwargs):
    return tuple(sorted(kwargs.items()))

def unfreeze_kwargs(frozen_kwargs):
    return dict(frozen_kwargs)

def with_checkmark_message(msg, fn_call, log):
    try:
        result = fn_call()
        log.info(f'✅ {msg}')
        return result
    except Exception as e:
        log.error(f'❌ {msg}')
        raise

def verify_deps(**deps):
    "Make a target fail when one or more of its deps does"
    errors = {}
    for (k, v) in deps.items():
        if isinstance(v, dict):
            for (k2, v2) in v.items():
                if isinstance(v2, Error):
                    if not k in errors:
                        errors[k] = {}
                    errors[k][k2] = v2
        elif isinstance(v, Error):
            errors[k] = v
        # else drop the non-errors
    error_keys = ', '.join(sorted(errors.keys()))
    if len(errors) > 0:
        raise DependencyError(f'dependencies failed: {error_keys}')
    return deps

def verify_decryption_with_checkmark_message(
    msg: str,
    log: logging.Logger,
    plaintext_tally: PlaintextTally,
    all_guardian_pubkeys: dict[GuardianId, ElectionPublicKey],
    context: CiphertextElectionContext,
) -> bool:
    def verify_closure():
        result = verify_decryption(plaintext_tally, all_guardian_pubkeys, context)
        if not result.verified:
            raise Exception(result.message)
        return True
    return with_checkmark_message(msg, verify_closure, log)

def verify_assertion(msg, assertion, log):
    # wrapper is required because you can't `assert` inside a lambda
    def assertion_fn():
        try:
            assert assertion
        except AssertionError as e:
            raise Exception(f'false: {msg}')
    return with_checkmark_message(msg, assertion_fn, log)

def verify_public_record(
    results: ResultsCache,
    pubdir: str,
    log: logging.Logger,
    target: TargetName,
    **fmtargs
) -> Union[Error, Success]:
    "Wrap from_public_record with verification stuff"
    try:
        # If one of the kwargs is explicitly msg, that should be used.
        msg = fmtargs.pop('msg')
    except:
        # Otherwise, use target + fmtargs if any, and otherwise just target
        if len(fmtargs) == 0:
            msg = target
        else:
            msg = f'{target} {fmtargs}'
    try:
        result = with_checkmark_message(
            msg,
            lambda: from_public_record(pubdir, target, **fmtargs),
            log
        )
        return result
    except Exception as e:
        raise
