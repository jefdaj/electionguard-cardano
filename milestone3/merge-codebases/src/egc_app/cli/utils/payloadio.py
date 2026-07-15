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
class PayloadIO:
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
    prefix = f"{name}-"
    verb = {"in": "Read", "out": "Write"}[direction]
    group = _make_group(name, direction, required)

    factories = {
        "qr": lambda: group.option(
            f"--{prefix}qr", is_flag=True,
            help=f"{verb} a QR code via the camera / screen."),
        "qr-image": lambda: group.option(
            f"--{prefix}qr-image", type=click.Path(), metavar="PATH",
            help=f"{verb} a QR code as an image file."),
        "json": lambda: group.option(
            f"--{prefix}json", type=click.Path(), metavar="PATH",
            help=f"{verb} data as a JSON file."),
    }
    opts = [factories[m]() for m in mediums]
    for opt in reversed(opts):           # reverse -> declaration order in --help
        f = opt(f)
    return f


def resolve_payload(name, direction, params) -> PayloadIO:
    """Pop this group's params out of `params` (mutates) and build a PayloadIO."""
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
    return PayloadIO(name, direction, medium, path)


# ---- read / write --------------------------------------------------------

def read_payload(pio: PayloadIO, decode_cls=None):
    match pio.medium:
        case "qr":       return scan_qrcode(decode_cls=decode_cls)
        case "qr-image": return decode_qr_image(pio.path)  # TODO -> decode_cls?
        case "json":
            with pio.path.open("r") as f:
                return decode_cls.from_json(_json.load(f))


def write_payload(pio: PayloadIO, obj: Any, exist_ok=True) -> None:
    if pio.path is not None and pio.path.exists() and not exist_ok:
        raise click.UsageError(f"path already exists: {pio.path}")
    match pio.medium:
        case "qr":       print_qrcode(obj)
        case "qr-image": save_qrcode(obj, pio.path)
        case "json":
            with pio.path.open("w") as f:
                _json.dump(obj, f)


# ---- public decorators ---------------------------------------------------

def payload_load(name, decode_cls, mediums, *, required=True):
    """`in` direction: gather args, read + parse to `decode_cls`, inject as `name`."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            pio = resolve_payload(name, "in", params)      # pops name_* keys
            params[name] = read_payload(pio, decode_cls=decode_cls)
            return fn(**params)
        return _add_options(wrapper, name, mediums, "in", required)
    return decorator


def payload_save_arg(name, mediums, *, required=True):
    """`out` direction: gather args into a PayloadIO, inject as `name`."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            params[name] = resolve_payload(name, "out", params)
            return fn(**params)
        return _add_options(wrapper, name, mediums, "out", required)
    return decorator

