import dataclasses
from deepdiff import DeepDiff
import logging

LOG = logging.getLogger(__name__)

def _deepdiff_prep(obj):
    if isinstance(obj, bytes):
        try:
            return obj.decode("utf-8", errors="replace")
        except Exception as e:
            # Will happen at least with CID fields, maybe others.
            LOG.error(f'failed to decode bytes: {obj}')
            return obj
    if isinstance(obj, dict):
        return {k: _deepdiff_prep(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set, frozenset)):
        return type(obj)(_deepdiff_prep(i) for i in obj)
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        # This was problematic with the fancy PlutusData types
        # return dataclasses.replace(obj, **{
        #     f.name: _deepdiff_prep(getattr(obj, f.name))
        #     for f in dataclasses.fields(obj)
        # })
        return obj
    # attrs support
    try:
        import attr
        if attr.has(type(obj)):
            return attr.evolve(obj, **{
                f.name: _deepdiff_prep(getattr(obj, f.name))
                for f in attr.fields(type(obj))
            })
    except ImportError:
        pass
    return obj

def safe_deepdiff(a, b, *args, **kwargs):
	# Workaround for: https://github.com/qlustered/deepdiff/issues/472
	return DeepDiff(
		_deepdiff_prep(a),
		_deepdiff_prep(b),
        *args, **kwargs
	)
