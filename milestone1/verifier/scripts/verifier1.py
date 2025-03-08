#!/usr/bin/env python3

import click

from dataclasses import dataclass
from typing import Dict, Optional, List
from pprint import pprint
from collections import defaultdict

from utils import (
    build_election,
    load_submitted_ballots,
    load_cast_ballots,
    load_tally_shares,
    load_spoiled_shares,
    load_spoiled_results,
    load_guardian_pubkeys_dict,
    load_spoiled_ballots,
    to_public_record,
    from_public_record,
)


from electionguard.ballot import CiphertextBallot, SubmittedBallot
from electionguard.election import CiphertextElectionContext
from electionguard.key_ceremony import ElectionPublicKey
from electionguard.manifest import (
    InternalManifest,
    Manifest,
)
from electionguard.type import GuardianId
from electionguard.tally import PlaintextTally, CiphertextTally

from electionguard_verify import *

import json
from pygments import highlight, lexers, formatters

import logging
import sys
from io import StringIO

from electionguard_cli.cli_steps.cli_step_base import CliStepBase


### utils ###

# based on:
# docs.python.org/3/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging
# gist.github.com/66Ton99/b13c2867adef506554a4
class CaptureLog:

    def __init__(self, level=None, close=True):
        self.logger = logging.getLogger('electionguard')
        self.log_buffer = StringIO()
        self.handler = logging.StreamHandler(self.log_buffer)
        self.level = level
        self.close = close

    def __enter__(self):

        # remove original handlers and add the temporary one
        self.old_handlers = list(h for h in self.logger.handlers)
        self.logger.handlers.clear()
        self.logger.addHandler(self.handler)

        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)

        # for use within the context manager block
        return self.log_buffer

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.close:
            self.handler.close()

        # remove temporary handler and put back the originals
        self.logger.handlers.clear()
        for h in self.old_handlers:
            self.logger.addHandler(h)

        # implicit return of None => don't swallow exceptions

# TODO unify with the one in local-election scripts
def print_colorful_json_obj(obj):
    # based on https://stackoverflow.com/a/32166163
    formatted_json = json.dumps(obj, indent=2)
    colorful_json = highlight(
        formatted_json,
        lexers.JsonLexer(),
        formatters.TerminalFormatter()
    )
    print(colorful_json)

# TODO pass cfg here
def summarize_errors(errors) -> int:
    # prints and then returns a summary dict + n_errors
    errors = {k:v for (k,v) in errors.items() if len(v) > 0}
    n_errors = sum(
        1 if isinstance(v, str) else len(v)
        for v in errors.values()
    )
    if n_errors > 0:
        print(f'Found {n_errors} irregularities...\n')
        print_colorful_json_obj(errors)
        print('The election could NOT be verfified! ⛔')
    else:
        print('No irregularities found.')
        print('The election has been verfified! 🎉')
        print()
    return (errors, n_errors)

def abort(error_dict):
    print('Unable to finish verification.')
    summarize_errors(error_dict)
    raise SystemExit(1)


### verify ###

def verify_load_ballots(public_dir, load_fn, error_dict, error_name):
    try:
        ballots = load_fn(public_dir)
        ballot_ids = set(b.object_id for b in ballots)
        n_loaded = len(ballot_ids)
        return (ballots, ballot_ids, n_loaded)
    except FileNotFoundError as e:
        error_dict[error_name]['verify_load_ballots'] = str(e)
        raise

def verify_ciphertext_ballots(ballots, header_msg, manifest, context) -> int:
    print(header_msg)
    errors = {}
    for ballot in ballots:
        print(f'  {ballot.object_id}', end=' '),
        with CaptureLog(level=logging.DEBUG) as log:
            result = verify_ballot(ballot, manifest, context)
            if result.verified:
                print('✅')
            else:
                # print(f'ERROR {ballot.object_id} failed verification!')
                print('❌')
                msgs = []
                if result.message is not None:
                    msgs.append(result.message)
                msgs.append(log.getvalue().strip())
                errors[ballot.object_id] = ' '.join(msgs)
    print()
    return errors

def verify_predicate(predicate, header_msg, error_dict, error_name):
    try:
        print(header_msg + '', end=' ')
        assert predicate
        print('✅')
    except Exception as e:
        print('❌')
        error_dict[error_name] = str(e)

def verify_ballots(public_dir, errors, manifest, context):
    verify_header = 'Verification steps'
    csb = CliStepBase() # prints in electionguard_cli style
    csb.print_header(verify_header)
    print()

    all_ballots_loaded = True

    # TODO handle these not existing too? might be silent unless they're all missing
    submitted_ballots = load_submitted_ballots(public_dir)
    submitted_ballot_ids = set(b.object_id for b in submitted_ballots)
    n_submitted = len(submitted_ballot_ids)

    try:
        # if this fails we just get one verify_load_ballots error
        # (No such file or directory)
        print('loading cast ballots and checking their formats', end=' ')
        (cast_ballots, cast_ballot_ids, n_cast) = verify_load_ballots(
            public_dir, load_cast_ballots, errors, 'cast_ballots'
        )
        print('✅')
        # if this fails we get a dict of ballot ids to irregularities
        errors['cast_ballots'] = verify_ciphertext_ballots(
            cast_ballots,
            f'verifying the ciphertext of the {n_cast} cast ballots:',
            manifest, context
        )
    except:
        print('❌')
        all_ballots_loaded = False

    try:
        print('loading spoiled ballots and checking their formats', end=' ')
        (spoiled_ballots, spoiled_ballot_ids, n_spoiled) = verify_load_ballots(
            public_dir, load_spoiled_ballots, errors, 'spoiled_ballots'
        )
        print('✅')
        errors['spoiled_ballots'] = verify_ciphertext_ballots(
            spoiled_ballots,
            f'verifying the ciphertext of the {n_spoiled} spoiled ballots:',
            manifest, context
        )
    except:
        print('❌')
        all_ballots_loaded = False

    if not all_ballots_loaded:
        abort(errors)
        print('still going after abort?')

    else:
        # TODO move this to the end, after spoiled ballot decryptions?
        print('double checking that all ballots are accounted for:')

        verify_predicate(
            n_cast + n_spoiled == n_submitted,
            f'  {n_cast} ballots cast + {n_spoiled} spoiled = {n_submitted} submitted',
            errors, 'ballots_accounted_for'
        )

        verify_predicate(
            cast_ballot_ids.union(spoiled_ballot_ids) == submitted_ballot_ids,
            '  set(cast IDs) + set(spoiled IDs) = set(submitted IDs)',
            errors, 'ballots_accounted_for'
        )

        # for later comparisons
        return (spoiled_ballot_ids, n_spoiled, cast_ballots)

def verify_spoiled_results(public_dir, errors, guardian_pubkeys, context):
    # TODO assert that the len here matches spoiled_ballots

    print('loading decrypted ballots and checking their formats', end=' ')
    # TODO verify_load_ballots here?
    try:
        spoiled_results = load_spoiled_results(public_dir)
        print('✅')
    except Exception as e:
        print('❌')
        errors['load_spoiled_results'] = str(e)
        raise

    print('verifying spoiled ballot decryptions:')
    for spoiled_result in spoiled_results:
        print(f'  {spoiled_result.object_id}', end=' ')
        try:
            with CaptureLog(level=logging.DEBUG) as log:
                result = verify_decryption(spoiled_result, guardian_pubkeys, context)
                if result.verified:
                    print('✅')
                else:
                    print('❌')
                    msgs = []
                    if result.message is not None:
                        msgs.append(result.message)
                    msgs.append(log.getvalue().strip())
                    errors[spoiled_result.object_id] = ' '.join(msgs)
        except Exception as e:
            print('❌')
            errors[spoiled_result.object_id] = str(e)
            raise
    spoiled_result_ids = set(r.object_id for r in spoiled_results)
    n_spoiled_results = len(spoiled_result_ids)
    return (spoiled_result_ids, n_spoiled_results)

def verify_tally(public_dir, errors, manifest, cast_ballots, guardian_pubkeys, context):
    print('verifying the final tally:')

    try:
        print('  loading tally and checking its format', end=' ')
        tally_result = from_public_record(public_dir, 'plaintext_tally')
        print('✅')
    except Exception as e:
        print('❌')
        errors['final_tally'] = str(e)
        tally_verified = False

    try:
        n_cast = len(cast_ballots)
        print(f'  verifying aggregation of {n_cast} cast ballots into tally', end=' ')
        verify_aggregation(cast_ballots, tally_result, manifest, context)
        print('✅')
    except Exception as e:
        print('❌')
        errors['final_tally'] = str(e)
        tally_verified = False

    try:
        print('  verifying tally decryption', end=' ')
        verify_decryption(tally_result, guardian_pubkeys, context)
        print('✅')
        tally_verified = True
        # TODO produce 8_summary.json and print here
    except Exception as e:
        print('❌')
        errors['final_tally'] = str(e)
        tally_verified = False

# TODO pass cfg here
def verify_election(public_dir, verifier_id):

    # custom dict to build up a report
    # TODO codify it as a class?
    errors = defaultdict(lambda: {})

    try:
        manifest  = from_public_record(public_dir, 'manifest')
    except Exception as e:
        errors['manifest']['from_public_record'] = str(e)
        abort(errors)

    try:
        details = from_public_record(public_dir, 'ceremony_details')
    except Exception as e:
        errors['ceremony']['from_public_record'] = str(e)
        abort(errors)

    try:
        joint_key = from_public_record(public_dir, 'joint_key')
    except Exception as e:
        errors['election_details']['from_public_record'] = str(e)
        abort(errors)

    try:
        (_, _, context) = build_election(details, manifest, joint_key)
    except Exception as e:
        errors['election_details']['build_election'] = str(e)
        abort(errors)

    try:
        (spoiled_ids, n_spoiled, cast_ballots) = verify_ballots(
            public_dir, errors, manifest, context
        )
        ballots_verified = True
    except SystemExit:
        raise
    except Exception as e:
        print(str(e))
        ballots_verified = False

    try:
        guardian_pubkeys = load_guardian_pubkeys_dict(public_dir)
    except SystemExit:
        raise
    except Exception as e:
        errors['guardian_pubkeys']['load_guardian_pubkeys'] = str(e)
        abort(errors)

    print()

    # TODO this also goes under verify_ballots because it depends on those results
    # TODO why aren't these causing overall failures like they should?
    try:
        (spoiled_result_ids, n_spoiled_results) = verify_spoiled_results(
            public_dir, errors['spoiled_results'], guardian_pubkeys, context
        )
        # TODO put this in the same section with the earlier "all accounted for" checks?
        verify_predicate(
            n_spoiled_results == n_spoiled,
            f'  {n_spoiled_results} decrypted ballots = {n_spoiled} spoiled',
            errors, 'spoiled_results'
        )
        verify_predicate(
            spoiled_result_ids == spoiled_ids,
            '  set(decrypted IDs) + set(spoiled IDs)',
            errors, 'ballots_accounted_for',
        )
        spoiled_results_verified = True
    except Exception as e:
        errors['spoiled_results'] = str(e)
        spoiled_results_verified = False
        raise

    print()

    verify_tally(public_dir, errors, manifest, cast_ballots, guardian_pubkeys, context)

    print()

    (errors, n_errors) = summarize_errors(errors)
    summarize_results(public_dir, verifier_id, errors, n_errors)


### summarize ###

# TODO include summarize_errors here if there are any
# TODO make sure that happens even if any of the files fail to load
# TODO move above the main verify_election function
def summarize_results(
    public_dir,
    verifier_id,
    errors,
    n_errors,
):

    # no particular format, except it must be json-serializable
    summary = defaultdict(lambda: {})

    csb = CliStepBase() # prints in electionguard_cli style

    manifest        = from_public_record(public_dir, 'manifest')
    tally_result    = from_public_record(public_dir, 'plaintext_tally')
    spoiled_results = load_spoiled_results(public_dir)

    selection_names = manifest.get_selection_names("en")
    contest_names   = manifest.get_contest_names()

    spoiled_header = 'Individual spoiled ballots'
    csb.print_header(spoiled_header)
    print()
    spoiled_summaries = {}
    for spoiled_result in spoiled_results:
        ballot_id = spoiled_result.object_id
        short_id  = ballot_id[ballot_id.find('-')+1:]
        print(short_id)
        ballot_summary = []
        for contest in spoiled_result.contests.values():
            question = contest_names.get(contest.object_id)
            selected = [
                selection_names[selection.object_id]
                for selection in contest.selections.values()
                if selection.tally > 0
            ]
            assert len(selected) < 2 # for a one of m contest
            try:
                answer = selected[0]
            except IndexError:
                answer = 'No answer' # TODO is this allowed?
            print(f'  {question} {answer}')
            contest_summary = {question: answer}
            ballot_summary.append(contest_summary)
        spoiled_summaries[short_id] = ballot_summary
        print()

    tally_header = "Final tally of cast ballots"
    csb.print_header(tally_header)
    tally_summary = []
    contest_summaries = []
    for tally_contest in tally_result.contests.values():
        contest_name = contest_names.get(tally_contest.object_id)
        contest_summary = {
            'question': contest_name,
            'votes': {},
        }
        csb.print_section(contest_name)
        values = list(tally_contest.selections.values())
        values.sort(key=lambda v: v.tally, reverse=True)
        for selection in values:
            name = selection_names[selection.object_id]
            csb.print_value(f"  {name}", selection.tally)
            contest_summary['votes'][name] = selection.tally
        tally_summary.append(contest_summary)

    # save summary json
    # no particular format, except it must be a json-serializable dict
    summary = {
        'Verified': n_errors == 0,
        'Irregularities': errors,
        tally_header  : tally_summary,
        spoiled_header: spoiled_summaries,
    }
    to_public_record(public_dir, 'summary', summary, verifier_id=verifier_id)
    print()



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
    help="Unique ID for this  in the ceremony",
    type=click.STRING,
)
def VerifyCommand(
    public_dir: str,
    verifier_id: str,
) -> None:
    """Verify all public election artifacts.
    """
    # TODO parse and pass cfg here
    verify_election(public_dir, verifier_id)


@click.group
def cli() -> None:
    pass

cli.add_command(VerifyCommand)

if __name__ == '__main__':
    cli()
