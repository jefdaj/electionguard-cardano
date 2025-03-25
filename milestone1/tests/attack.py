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


### attack functions ###

def rm_submitted_ballot():
    raise NotImplementedError

def rm_cast_ballot():
    raise NotImplementedError

def rm_spoiled_ballot():
    raise NotImplementedError

ATTACK_FUNCTIONS = [
    rm_submitted_ballot,
    rm_cast_ballot,
    rm_spoiled_ballot,
]
