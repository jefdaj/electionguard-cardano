from fastapi import Request
from egc import *

# TODO is this a reasonable state pattern?

def get_state(request: Request):
    return request.app.state

# state is a plain namespace (starlette.datastructures.State).
# Fine for holding pools, clients, config, and simple mutable values.
def setup_state(state, config):
    state.config = config
    state.wallet = None
    reset_election_state(state)

def reset_election_state(state):
    # Resets the parts of the state that depend on the current election.
    # Should NOT reset the wallet.
    state.node = ObserverNode(
        role_index = 1, # TODO pass this in? or ignore/deprecate
        wallet = state.wallet,
    )

def teardown_state(state):
    if getattr(state, 'node', None) is not None:
        state.node.stop()
