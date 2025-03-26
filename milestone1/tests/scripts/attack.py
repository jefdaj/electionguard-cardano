#!/usr/bin/env python3

# TODO rethink this! it would be much cooler if attacks can happen throughout
# the election. two ideas about how to implement that:
# 1. something with hypothesis' stateful testing
# 2. add attacks to the main election config and run them during it 

# TODO here's a good simple idea how to implement option 2:
# - add AttacksConfig to RunConfig
# - factor projectconfig() out of given_valid_election and make an attack version
# - one fn each using different composite generators: honest and attack
# - work attacks into election using a Dict[election step, List[attack fn]]
#   - GO WITH THIS FIRST: rewrite election fn to use a list of str fn names and apply matching attacks?
#     - pro: easier to edit files in unexpected ways directly as files
#     - pro: less messing with regular non-attack-related code
#   - or pass attacks into the actual fns and apply them during the main operations?

import random

### attack functions ###
#
# These attack functions will be run between regular steps in `election.py`.
# They should be no-ops except when the `step` argument indicates that the
# step(s) whose output files should be changed have just run. The `index` is
# for disambiguating when the same attack is randomly chosen to be run more
# than once.
# TODO how do we use index exactly?

def rm_submitted_ballot(cfg, log, step, index):
    if step != 'vote_commit_all':
        return
    log.info(f'running attack {index}: rm_submitted_ballot')
    random.seed(index)
    # TODO finish writing

def rm_cast_ballot(cfg, log, step, index):
    if step != 'vote_reveal_all':
        return
    log.info(f'running attack {index}: rm_cast_ballot')
    random.seed(index)
    # TODO finish writing

def rm_spoiled_ballot(cfg, log, step, index):
    if step != 'vote_reveal_all':
        return
    log.info(f'running attack {index}: rm_spoiled_ballot')
    random.seed(index)
    # TODO finish writing

ATTACK_FUNCTIONS = [
    rm_submitted_ballot,
    rm_cast_ballot,
    rm_spoiled_ballot,
]


### cli ###

@click.command("attack")
@click.option(
    "--public-dir",
    prompt="Public records directory",
    help="The location of a directory into which will be placed all public records. "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--private-dir",
    prompt="Private records directory",
    help="The location of a directory into which will be placed the guardian's private keys "
    + "This folder should be protected. Existing files will be overwritten.",
    type=click.Path(exists=False, dir_okay=True, file_okay=False, resolve_path=True),
)
@click.option(
    "--attacker-id",
    prompt="Unique ID for this attacker",
    help="Used to decide which container to run the attack script from",
    type=click.STRING,
)
@click.option(
    "--attack-fn",
    prompt="Attack function name",
    help="Which attack to run",
    type=click.STRING,
)
@click.option(
    "--logfile",
    prompt="Logfile (default: stdout)",
    help="Where to log printed messages",
    type=click.STRING,
)
@click.option(
    "--random-seed",
    prompt="Random seed",
    help="Used when picking files to edit",
    type=click.INT,
)
def AttackCommand(
    public_dir: str,
    private_dir: str,
    attacker_id: str,
    attack_fn: str,
    random_seed: int,
    logfile: Optional[str],
) -> None:
    # TODO parse and pass cfg here?
    log.info(f'locals: {locals()}')
    log = init_log(logfile, logging.INFO)

@click.group
def cli() -> None:
    pass

cli.add_command(AttackCommand)

if __name__ == '__main__':
    cli()
