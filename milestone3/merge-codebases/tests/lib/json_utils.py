import json

import dataclasses

def fancy_dumps(obj, indent=2, width=60, _level=0):
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
