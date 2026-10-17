from dataclasses import replace, is_dataclass
from deepdiff import DeepDiff
import logging

LOG = logging.getLogger(__name__)

# monkeypatch to work around:
# https://github.com/qlustered/deepdiff/issues/472
# TODO contribute upstream
import deepdiff.model as _dm
_orig = _dm.stringify_element
def _patched(param, quote_str=None):
    if isinstance(param, bytes):
        param = repr(param)  # keeps b'...' readable rather than mangling it
    return _orig(param, quote_str=quote_str)
_dm.stringify_element = _patched

def safe_deepdiff(a, b, *args, **kwargs):
    # Just makes sure we apply the patch before using.
    return DeepDiff(a, b, *args, **kwargs)

def deep_replace(obj, path, value):
    "Usage: new = deep_replace(root, 'a.b.c', 42)"
    key, _, rest = path.partition(".")
    if rest:
        value = deep_replace(getattr(obj, key), rest, value)
    return replace(obj, **{key: value})

