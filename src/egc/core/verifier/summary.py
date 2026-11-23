from .types import *

import logging
LOG = logging.getLogger(__name__)


def simplify_and_partition(results: ResultsCache) \
        -> (Successes, Errors, VerifiedBools):

    successes: Successes = {}
    errors: Errors = {}
    bools: VerifiedBools = {}

    # simplify
    results2 = {}
    for (k,v) in results.items():

        # special cases/warts
        if k == 'ballot_cast':
            k = 'cast_notice'

        # remove trivial kwargs
        if list(v.keys()) == [()]:
            v2 = list(v.values())[0]
            results2[k] = v2

        # convert kwargs to their public record basenames
        else:
            results2[k] = {}
            for (k2, v2) in v.items():
                fmtargs = unfreeze_kwargs(k2)
                fname = record_basename(k, **fmtargs)
                results2[k][fname] = v2

    # partition
    for (target_name, result) in results2.items():
        if isinstance(result, Error):
            errors[target_name] = result
            bools[target_name] = False
            # LOG.info(f'{target_name} goes in errors')
            LOG.info(f'{target_name} error: {result}')
        elif isinstance(result, dict):
            successes_dict = {
                k:v for (k,v)
                in result.items()
                if not isinstance(v, Error)
            }
            errors_dict = {
                k:v for (k,v)
                in result.items()
                if isinstance(v, Error)
            }
            if len(errors_dict) > 0:
                errors[target_name] = errors_dict
                # LOG.info(f'some of {target_name} goes in errors')
            if len(successes_dict) > 0:
                successes[target_name] = successes_dict
                # LOG.info(f'some of {target_name} goes in successes')
        else:
            # should be a single success or a list
            successes[target_name] = result
            bools[target_name] = True
            # LOG.info(f'{target_name} goes in successes')

    LOG.debug(f'successes keys: {successes.keys()}')
    LOG.debug(f'errors keys: {errors.keys()}')

    return (successes, errors, bools)


def summarize_results_sofar(
    successes: Successes,
    errors: Errors,
    bools: VerifiedBools,
) -> (dict, int):
    n_errors = sum(
        1  if isinstance(v, Error) else len(v)
        for v in errors.values()
    )

    # No particular format yet, except it must be a json-serializable dict.
    # Will be codified later to make it simple to adjudicate whether a summary is valid.
    # TODO codify it as a dataclass?
    summary = defaultdict(lambda: {})

    tally_header   = "Final tally of cast ballots"
    spoiled_header = 'Individual spoiled ballots'
    spoiled_summaries = {}
    try:

        LOG.info('\n' + spoiled_header + ':')

        spoiled_results = successes['all_spoiled_results']
        manifest        = successes['manifest']
        selection_names = manifest.get_selection_names("en")
        contest_names   = manifest.get_contest_names()

        for spoiled_result in spoiled_results:
            LOG.info('')
            if isinstance(spoiled_result, Error):
                continue
            ballot_id = spoiled_result.object_id
            short_id  = ballot_id[ballot_id.find('-')+1:]
            LOG.info(short_id)
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
                LOG.info(f'  {question} {answer}')
                contest_summary = {question: answer}
                ballot_summary.append(contest_summary)
            spoiled_summaries[short_id] = ballot_summary

        LOG.info('\n' + tally_header + ':\n')
        tally_result    = successes['plaintext_tally']
        tally_summary = []
        contest_summaries = []
        for tally_contest in tally_result.contests.values():
            contest_name = contest_names.get(tally_contest.object_id)
            contest_summary = {
                'question': contest_name,
                'answers': {},
            }
            LOG.info(contest_name)
            values = list(tally_contest.selections.values())
            values.sort(key=lambda v: v.tally, reverse=True)
            for selection in values:
                name = selection_names[selection.object_id]
                LOG.info(f"  {selection.tally} {name}")
                contest_summary['answers'][name] = selection.tally
            tally_summary.append(contest_summary)

    except Exception as e:
        tally_summary     = 'Unable to summarize tally'
        spoiled_summaries = 'Unable to summarize individual spoiled ballots'
        LOG.error('Unable to summarize individual spoiled ballots')
        LOG.error(e)
        n_errors += 1 # TODO is this a reasonable way to do it?

    # No particular format yet, except it must be a json-serializable dict.
    # Will be codified later to make it simple to adjudicate whether a summary is valid.
    summary = {
        'Verified': bools,
        'Errors': errors,
        tally_header  : tally_summary,
        spoiled_header: spoiled_summaries,
    }
    return (summary, n_errors)

def summarize_results_final(
    successes: Successes,
    errors: Errors,
    bools: VerifiedBools,
    pubdir: str,
    verifier_id: str,
) -> int:
    """This version saves the final JSON in the public records dir,
    then prints an overall summary message.
    """
    summary = summarize_results_sofar(successes, errors, bools)
    to_public_record(pubdir, 'summary', summary, verifier_id=verifier_id)
    LOG.info('')
    if n_errors == 0:
        LOG.info('🎉 The election has been verified!')
    else:
        msgs = [
            'The election could NOT be verified!',
            f'There were {n_errors} errors.',
            f'See {verifier_id}.json for details.',
        ]
        LOG.error('\n'.join('⛔ ' + m for m in msgs))
    return n_errors # TODO and dict?
