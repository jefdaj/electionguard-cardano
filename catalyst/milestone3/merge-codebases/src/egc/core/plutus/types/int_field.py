import re
from dataclasses import dataclass
from pycardano import PlutusData


# Field names that should be treated as non-negative ints in PlutusData types.
# TODO also constrain upper limits?
INT_FIELDS = frozenset({'guardian_number', 'backup_order', 'device_number'})


def coerce_int(value: int | str | bytes) -> int:
    """Accept int, str, or bytes; validate; return non-negative int."""
    if isinstance(value, bool):
        # bool is an int subclass—reject to avoid True/False sneaking through
        raise TypeError("expected int, got bool")
    elif isinstance(value, int):
        n = value
    elif isinstance(value, (str, bytes)):
        s = value.decode('utf-8') if isinstance(value, bytes) else value
        try:
            n = int(s)
        except ValueError as e:
            raise ValueError(f"invalid integer: {s!r}") from e
    else:
        raise TypeError(
            f"expected int, str, or bytes, got {type(value).__name__}"
        )

    if n < 0:
        raise ValueError(f"must be non-negative, got {n}")
    return n


class IntFieldMixin:
    """
    Mixin for PlutusData subclasses with one or more integer fields.
    Coerces str/bytes -> int and validates in __post_init__.

    Must come BEFORE PlutusData in the MRO so this __post_init__ runs.
    """

    def __post_init__(self):
        for field_name in INT_FIELDS:
            if hasattr(self, field_name):
                current = getattr(self, field_name)
                object.__setattr__(self, field_name, coerce_int(current))
        super_post = getattr(super(), '__post_init__', None)
        if super_post is not None:
            super_post()
