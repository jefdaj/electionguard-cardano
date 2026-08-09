import json
import cattrs
import dataclasses
from deepdiff import DeepDiff


def raw_fancy_dumps(obj, indent=2, width=70, _level=0) -> str:
    "Like json.dumps, but refrains from indenting things that fit on one line."

    pad = " " * (indent * (_level + 1))
    close_pad = " " * (indent * _level)

    if isinstance(obj, dict):
        if not obj:
            return "{}"
        compact = json.dumps(obj, separators=(", ", ": "))
        if len(compact) + len(pad) <= width:
            return compact
        items = [f'{pad}{json.dumps(k)}: {raw_fancy_dumps(v, indent, width, _level+1)}'
                 for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + close_pad + "}"

    if isinstance(obj, list):
        if not obj:
            return "[]"
        # print(f'list obj: {obj}')
        compact = json.dumps(obj, separators=(", ", ": ")) # TODO fails to fancy dump within this?
        # print(f'compact: {compact}')
        # raise Exception
        if len(compact) + len(pad) <= width:
            return compact
        items = [f'{pad}{raw_fancy_dumps(v, indent, width, _level+1)}' for v in obj]
        return "[\n" + ",\n".join(items) + "\n" + close_pad + "]"

    return json.dumps(obj)

def make_converter():
    c = cattrs.Converter(forbid_extra_keys=True)
    c.register_structure_hook(
        str | int,
        lambda v, _: v if isinstance(v, (str, int)) else int(v),
    )
    def has_to_dict(cls) -> bool:
        return isinstance(cls, type) and callable(getattr(cls, "to_dict", None))
    def has_from_dict(cls) -> bool:
        return isinstance(cls, type) and callable(getattr(cls, "from_dict", None))
    # factory receives the concrete type, returns the hook
    c.register_unstructure_hook_factory(
        has_to_dict,
        lambda cls: lambda obj: obj.to_dict(c.unstructure),
    )
    c.register_structure_hook_factory(
        has_from_dict,
        lambda cls: lambda data, _: cls.from_dict(data, c.structure),
    )
    return c

# TODO subclass instead?
JSON_CONVERTER = make_converter()

# TODO rename/refactor
def fancy_raw(obj):
    return JSON_CONVERTER.unstructure(obj)

# TODO rename to avoid confusion with raw_fancy_dumps (which doesn't need exporting)
def fancy_dumps(obj):
    "Encode a structured type as a str."
    # TODO unify with the to/from raw pattern in electionguard?
    h = JSON_CONVERTER.get_unstructure_hook(type(obj))
    raw = fancy_raw(obj)
    # return json.dumps(raw)
    return raw_fancy_dumps(raw)

def fancy_loads(obj_type, obj_json_str):
    "Decode a structured type from a str."
    # TODO unify with the to/from raw pattern in electionguard?
    raw = json.loads(obj_json_str)
    return JSON_CONVERTER.structure(raw, obj_type)


def assert_json_roundtrip(cfg):
    tmp_str = fancy_dumps(cfg)
    # tmp_str = json.dumps(dataclasses.asdict(cfg))
    cfg2 = fancy_loads(type(cfg), tmp_str)
    if cfg != cfg2:
        print(f'cfg: {cfg}')
        print(f'tmp_str: {tmp_str}')
        print(f'cfg2: {cfg2}')
        diff = DeepDiff(cfg, cfg2)
        print(f'diff: {diff}')
    assert cfg == cfg2
