from .utils import freeze_kwargs
from ..plutus.types import record as r
from ..plutus.types import ChannelId
from .types import *
from . import dag # for looking up verify_* functions
from pathlib import Path

import logging
LOG = logging.getLogger(__name__)

# TODO version of verify_public_record here that starts from the record metadata directly?

def verify_target(
    results: ResultsCache,
    pubdir: str,
    # log: logging.Logger,
    target: TargetName,
    **kwargs
):
    """
    Main verify function that calls the others with caching etc
    `results` is the main program state
    `pubdir` is the public_records dir
    `pubrec` is a key in the PUBLIC_RECORDS map
    """

    kwargs_frozen = freeze_kwargs(kwargs)

    # memoize
    # note this could sort of be done using functools.cache,
    # except that wouldn't also accumulate errors
    if target in results:
        if kwargs_frozen in results[target]:
            result = results[target][kwargs_frozen]
            return result

    # find and call the verify_ function,
    # capturing logs + errors
    # verify_fn = globals()[f'verify_{target}']
    verify_fn = getattr(dag, target, None)
    if verify_fn is None:
        raise ValueError(f"Unknown verifier: {target}")
    with CaptureLog(level=logging.DEBUG) as log2:
        try:
            result = verify_fn(results, pubdir, **kwargs)
        except Exception as e:
            msgs = [str(e)]
            msgs.append(log2.getvalue().strip())
            result = Error(' '.join(msgs).strip())
            # print(f'err during {verify_fn.__name__}: "{result}"')

    # cache result
    if not target in results:
        results[target] = {}
    results[target][kwargs_frozen] = result

    return result


# TODO rewrite as a class for use from a node
# def main(pubdir, log, verifier_id):
# 
#     # main program state
#     # accumulates successful result objects and error messages
#     results: ResultsCache = {}
# 
#     # these partially overlap, which is fine
#     verify(results, pubdir, log, 'gather_config')
#     verify(results, pubdir, log, 'all_ballots_submitted')
#     verify(results, pubdir, log, 'all_ballots_cast')
#     verify(results, pubdir, log, 'all_ballots_spoiled')
#     verify(results, pubdir, log, 'all_spoiled_results')
#     verify(results, pubdir, log, 'ballot_sets')
#     verify(results, pubdir, log, 'gather_tally')
#     verify(results, pubdir, log, 'gather_decryptions')
#     verify(results, pubdir, log, 'gather_election')
# 
#     (successes, errors, bools) = simplify_and_partition(results, log)
# 
#     n_errors = summarize_results(
#         successes, errors, bools,
#         pubdir, log, verifier_id,
#     )
# 
#     sys.exit(n_errors)

class Verifier:
    """Stateful verifier for use in a node."""

    def __init__(self, records_posting_dir: Path, verifier_id: ChannelId):
        self.records_posting_dir = records_posting_dir
        self.verifier_id = verifier_id
        self.results: ResultsCache = {}

    def verify_record_dict(self, metadata: r.PublicRecordMetadata, data: dict):
        "Called by RecordStore to verify data from IPFS before saving it to a file."
        pass

    def verify_target_by_name(self, target_name: str):
        """Called by Subscriber in response to phase changes.
        Mainly (only?) used for gather_* (phony) targets.
        """
        return verify(self.results, target_name)

    def summary_json(self):
        (successes, errors, bools) = simplify_and_partition(self.results)
        return summarize_results_sofar(
            successes, errors, bools,
        )

    def save_final_summary(self):
        (successes, errors, bools) = simplify_and_partition(self.results)
        return summarize_results_final(
            successes, errors, bools,
            records_posting_dir=self.records_posting_dir, verifier_id=self.verifier_id,
        )


# @click.command("verify")
# @click.option(
#     "--public-dir",
#     prompt="Public records directory",
#     help="The location of a directory into which will be placed all public records. "
#     + "This folder should be protected. Existing files will be overwritten.",
#     type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
# )
# @click.option(
#     "--verifier-id",
#     prompt="Unique ID for this verifier",
#     help="Used when saving the final JSON summary file",
#     type=click.STRING,
# )
# @click.option(
#     "--logfile",
#     prompt="Logfile (default: stdout)",
#     help="Where to log printed messages",
#     type=click.STRING,
# )
# def VerifyCommand(
#     public_dir: str,
#     verifier_id: str,
#     logfile: Optional[str],
# ) -> None:
#     """Verify all public election artifacts."""
#     # TODO parse and pass cfg here
#     log = init_log(logfile, logging.INFO)
#     try:
#         main(public_dir, log, verifier_id)
#     except Exception as e:
#         log.error(e)
#         raise
#         sys.exit(1)
# 
# @click.group
# def cli() -> None:
#     pass
# 
# cli.add_command(VerifyCommand)
# 
# if __name__ == '__main__':
#     cli()
# 
