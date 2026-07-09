from fastapi import Request

# app.state is a plain namespace (starlette.datastructures.State). Fine for
# holding pools, clients, config, and simple mutable values.
def get_state(request: Request):
    return request.app.state
