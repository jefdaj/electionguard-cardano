import json
import cattrs
import dataclasses
from deepdiff import DeepDiff


def fancy_dumps(obj, indent=2, width=80, _level=0) -> str:
    "Like json.dumps, but refrains from indenting things thta fit on one line."

    if hasattr(obj, 'to_dict'):
        # In case of types that need to control serialization more carefully.
        obj = obj.to_dict()
        s = json.dumps(obj)
        print(f'fancy_dumps s: {s}')
        return s

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
        # print(f'list obj: {obj}')
        compact = json.dumps(obj, separators=(", ", ": "))
        # print(f'compact: {compact}')
        if len(compact) + len(pad) <= width:
            return compact
        items = [f'{pad}{fancy_dumps(v, indent, width, _level+1)}' for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + close_pad + "]"

    return json.dumps(obj)


def fancy_loads(obj_type, obj_json_str):
    "Decode a structured type from a str."
    # TODO unify with the to/from raw pattern in electionguard?
    c = cattrs.Converter(forbid_extra_keys=True)

    def has_to_dict(cls) -> bool:
        return isinstance(cls, type) and callable(getattr(cls, "to_dict", None))

    def has_from_dict(cls) -> bool:
        return isinstance(cls, type) and callable(getattr(cls, "from_dict", None))

    # factory receives the concrete type, returns the hook
    c.register_unstructure_hook_factory(
        has_to_dict,
        lambda cls: lambda obj: obj.to_dict(),
    )

    c.register_structure_hook_factory(
        has_from_dict,
        lambda cls: lambda data, _: cls.from_dict(data),
    )

    return c.structure(json.loads(obj_json_str), obj_type)


def assert_json_roundtrip(cfg):
    tmp_str = fancy_dumps(cfg)
    cfg2 = fancy_loads(type(cfg), tmp_str)
    if cfg != cfg2:
        print(f'cfg: {cfg}')
        print(f'tmp_str: {tmp_str}')
        print(f'cfg2: {cfg2}')
        diff = DeepDiff(cfg, cfg2)
        print(f'diff: {diff}')
    assert cfg == cfg2
