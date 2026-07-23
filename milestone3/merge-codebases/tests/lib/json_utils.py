import json
import cattrs
import dataclasses


def fancy_dumps(obj, indent=2, width=80, _level=0) -> str:
    "Like json.dumps, but refrains from indenting things thta fit on one line."

    if hasattr(obj, 'to_dict'):
        # In case of types that need to control serialization more carefully.
        obj = obj.to_dict()

    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        obj = dataclasses.asdict(obj)          # recurses into nested dataclasses/tuples

    elif isinstance(obj, tuple):
        obj = list(obj)

    pad = " " * (indent * (_level + 1))
    close_pad = " " * (indent * _level)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        compact = json.dumps(obj, separators=(", ", ": "))
        if len(compact) + len(pad) <= width:
            return compact
        items = [f'{pad}{json.dumps(k)}: {fancy_dumps(v, indent, width, _level+1)}'
                 for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + close_pad + "}"

    if isinstance(obj, list):
        if not obj:
            return "[]"
        compact = json.dumps(obj, separators=(", ", ": "))
        if len(compact) + len(pad) <= width:
            return compact
        items = [f'{pad}{fancy_dumps(v, indent, width, _level+1)}' for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + close_pad + "]"

    return json.dumps(obj)


def fancy_loads(obj_type, obj_json_str):
    "Decode a structured type from a str."
    # TODO unify with the to/from raw pattern in electionguard?
    return cattrs.Converter().structure(json.loads(obj_json_str), obj_type)


def assert_json_roundtrip(cfg):
    tmp_str = fancy_dumps(cfg)
    cfg2 = fancy_loads(type(cfg), tmp_str)
    assert cfg == cfg2
