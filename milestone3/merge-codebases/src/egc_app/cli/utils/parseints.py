import click
import re

def parse_ints(s: str) -> set[int]:
    result = set()
    for tok in re.split(r"[,\s]+", s.strip()):
        if not tok:
            continue
        if "-" in tok:
            lo, hi = map(int, tok.split("-"))
            result.update(range(lo, hi + 1))
        else:
            result.add(int(tok))
    return result

class IntsType(click.ParamType):
    name = "ints"

    def convert(self, value, param, ctx):
        try:
            return parse_ints(value)
        except ValueError:
            self.fail(f"{value!r} is not a valid ints str", param, ctx)

INTS = IntsType()

def ints_arg(name="indices", dest="ints", required=False):
    """Decorator: positional arg(s) -> sorted list[int] passed as `dest`."""
    def decorator(f):
        @click.argument(name, nargs=-1, type=INTS, required=required)
        @click.pass_context
        def wrapper(ctx, *args, **kwargs):
            parsed = kwargs.pop(name)
            merged = set().union(*parsed) if parsed else set()
            kwargs[dest] = sorted(merged)
            return ctx.invoke(f, *args, **kwargs)
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        return wrapper
    return decorator
