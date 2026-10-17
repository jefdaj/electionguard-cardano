import signal
from contextlib import contextmanager
from dataclasses import replace
# import ast, inspect, hashlib, textwrap

class Terminated(Exception):
    pass

@contextmanager
def raise_on_signals(*signums):
    """Temporarily captures sigterm and handles it.

    Mainly used to be extra sure `arion down` runs.
    Example usage:

    with raise_on_signals(signal.SIGTERM, signal.SIGINT):
        try:
            ...
        finally:
            <run important cleanup here>
    """

    def _handler(signum, frame):
        raise Terminated(signum)

    previous = {}
    try:
        for s in signums:
            previous[s] = signal.signal(s, _handler)
        yield
    finally:
        for s, prev in previous.items():
            signal.signal(s, prev)


# def hash_ast(fn):
# 	"Hash functions so they can be included in HashedTestConfig."
#     tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
#     return hashlib.sha256(ast.dump(tree).encode()).hexdigest()
