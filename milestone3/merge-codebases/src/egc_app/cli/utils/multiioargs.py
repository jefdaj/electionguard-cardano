from egc.core.qrcodes import *

import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import json as _json

import click
import cloup
from cloup.constraints import mutually_exclusive, require_one

Direction = Literal["in", "out"]
Medium = Literal["qr", "qr-image", "json"]


@dataclass
class MultiIOArg:
    name: str
    direction: Direction
    medium: Medium
    path: Path | None = None


# ---- option construction -------------------------------------------------

def _make_group(name, direction, required):
    title = f"{name}: source" if direction == "in" else f"{name}: destination"
    return cloup.OptionGroup(
        title, constraint=require_one if required else mutually_exclusive
    )


def _add_options(f, name, mediums, direction, required):
    # prefix = f"{name}-"
    verb = {"in": "Read", "out": "Write"}[direction]
    cli_verbs = {
        "in" : {"qr": "scan-qr", "qr-image": "load-qr", "json": "load-json"},
        "out": {"qr": "show-qr", "qr-image": "save-qr", "json": "save-json"},
    }
    group = _make_group(name, direction, required)

    factories = {
        "qr": lambda: group.option(
            f"--{name}-{cli_verbs[direction]["qr"]}", is_flag=True,
            help=f"{verb} a QR code via the camera / screen."),
        "qr-image": lambda: group.option(
            f"--{name}-{cli_verbs[direction]["qr-image"]}", type=click.Path(), metavar="PATH",
            help=f"{verb} a QR code as an image file."),
        "json": lambda: group.option(
            f"--{name}-{cli_verbs[direction]["json"]}", type=click.Path(), metavar="PATH",
            help=f"{verb} data as a JSON file."),
    }
    opts = [factories[m]() for m in mediums]
    for opt in reversed(opts):           # reverse -> declaration order in --help
        f = opt(f)
    return f


def build_multi_arg(name, direction, params) -> MultiIOArg:
    """Pop this group's params out of `params` (mutates) and build a MultiIOArg."""
    prefix = f"{name}_"
    chosen = {}
    for k in [k for k in params if k.startswith(prefix)]:
        v = params.pop(k)
        if v:
            chosen[k[len(prefix):].replace("_", "-")] = v
    if len(chosen) != 1:
        raise click.UsageError(f"Exactly one {name} {direction}-source required.")
    medium, value = next(iter(chosen.items()))
    path = None if medium == "qr" else Path(value)
    return MultiIOArg(name, direction, medium, path)


# ---- read / write --------------------------------------------------------

# This could be part of the interface, but can normally be automated via
# multi_load_arg below.
def _multi_read(fio: MultiIOArg, decode_cls=None):
    match fio.medium:
        case "qr":       return scan_qrcode(decode_cls=decode_cls)
        case "qr-image": return decode_qr_image(fio.path)  # TODO -> decode_cls?
        case "json":
            with fio.path.open("r") as f:
                return decode_cls.from_json(_json.load(f))


# This can't be automated the same way, so it becomes par of the interface.
# Use inside a command after multi_save_arg has built the MultiIOArg.
def multi_save(fio: MultiIOArg, obj: Any, exist_ok=True) -> None:
    if fio.path is not None and fio.path.exists() and not exist_ok:
        raise click.UsageError(f"path already exists: {fio.path}")
    match fio.medium:
        case "qr":       print_qrcode(obj)
        case "qr-image": save_qrcode(obj, fio.path)
        case "json":
            with fio.path.open("w") as f:
                _json.dump(obj, f)


# ---- public decorators ---------------------------------------------------

def multi_load(name, decode_cls, mediums, *, required=True):
    """`in` direction: gather args, read + parse to `decode_cls`, inject as `name`."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            pio = build_multi_arg(name, "in", params)      # pops name_* keys
            params[name] = _multi_read(pio, decode_cls=decode_cls)
            return fn(**params)
        return _add_options(wrapper, name, mediums, "in", required)
    return decorator


def multi_save_arg(name, mediums, *, required=True):
    """`out` direction: gather args into a MultiIOArg, inject as `name`."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            params[name] = build_multi_arg(name, "out", params)
            return fn(**params)
        return _add_options(wrapper, name, mediums, "out", required)
    return decorator
