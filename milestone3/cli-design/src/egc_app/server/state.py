from fastapi import Request

# TODO is this a reasonable state pattern?

def get_state(request: Request):
    return request.app.state

# state is a plain namespace (starlette.datastructures.State).
# Fine for holding pools, clients, config, and simple mutable values.
def setup_state(state, config):
    state.config = config
    reset_election_state(state)

def reset_election_state(state):

    # Resets the parts of the state that depend on the current election:
    # - subscriber
    # - node (future)
    state.subscriber = None
    state.config['role'] = 'observer'

    # Leaves alone the parts that should persist:
    # - config
    # - wallet

def teardown_state(state):
    if getattr(state, 'subscriber', None) is not None:
        state.subscriber.stop()
