from fastapi import Request

# app.state is a plain namespace (starlette.datastructures.State). Fine for
# holding pools, clients, config, and simple mutable values.
def get_state(request: Request):
    return request.app.state

def reset_state(state):
    # Resets everything *except* it should preserve the wallet if any.
    state.subscriber = None
    if not hasattr(state, 'wallet'):
        # Don't clobber existing wallet
        state.wallet = None
