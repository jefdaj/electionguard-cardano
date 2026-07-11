from fastapi import Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

# app.state is a plain namespace (starlette.datastructures.State). Fine for
# holding pools, clients, config, and simple mutable values.
def get_state(request: Request):
    return request.app.state

# TODO does this need to go in deps rather than app?
def reset_election_state(state):

    # Resets the parts of the state that depend on the current election:
    # - subscriber
    # - node (future)
    state.subscriber = None

    # Leaves alone the parts that should persist:
    # - config
    # - wallet

TEMPLATES_DIR = str(Path(__file__).resolve().parent / "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
