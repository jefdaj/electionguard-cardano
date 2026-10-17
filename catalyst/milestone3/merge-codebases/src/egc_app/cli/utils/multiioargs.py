from egc.core.qrcodes import *

import functools
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
import json as _json
import time

from electionguard import serialize as eg_serialize

import click
import cloup
from cloup.constraints import mutually_exclusive, require_one
from cloup.constraints import RequireAtLeast  # "at least one across the group"


import logging

LOG = logging.getLogger(__name__)


Direction = Literal["in", "out"]
Medium = Literal["cam", "png", "txt", "json"]


@dataclass
class MultiIOArg:
    name: str
    direction: Direction
    medium: Medium
    path: Path | None = None


# ---- option construction -------------------------------------------------

def _make_group(name, direction, required):
    title = f"{name.capitalize()} input" if direction == "in" else f"{name} output"
    return cloup.OptionGroup(
        title, constraint=require_one if required else mutually_exclusive
    )


def _add_options(f, name, mediums, direction, required):
    # prefix = f"{name}-"
    help_text = {
        "in": {
            "cam":  "Scan QR code via the camera.",
            "png":  "Load QR code from a png file.",
            "txt":  "Load QR text (`egc:...`) from a file.",
            "json": "Load from a JSON file.", # TODO be clear this isn't a QR type
        },
        "out": {
            "cam":  "Show QR code so you can take a pic of it.",
            "png":  "Save QR code as a png file.",
            "txt":  "Save QR text (`egc:...`) to a file.",
            "json": "Save to a JSON file.", # TODO be clear this isn't a QR type
        },
    }[direction]
    # TODO any point in both txt and json long term?
    cli_verbs = {
        "in" : {"cam": "scan-qr", "png": "load-png", "json": "load-json", "txt": "load-txt"},
        "out": {"cam": "show-qr", "png": "save-png", "json": "save-json", "txt": "save-txt"},
    }[direction]
    group = _make_group(name, direction, required)

    factories = {
        "cam": lambda: group.option(
            f"--{name}-{cli_verbs["cam"]}", is_flag=True,
            help=help_text["cam"]),
        "png": lambda: group.option(
            f"--{name}-{cli_verbs["png"]}", type=click.Path(), metavar="PATH",
            help=help_text["png"]),
        "txt": lambda: group.option(
            f"--{name}-{cli_verbs["txt"]}", type=click.Path(), metavar="PATH",
            help=help_text["txt"]),
        "json": lambda: group.option(
            f"--{name}-{cli_verbs["json"]}", type=click.Path(), metavar="PATH",
            help=help_text["json"]),
    }
    opts = [factories[m]() for m in mediums]
    for opt in reversed(opts):           # reverse -> declaration order in --help
        f = opt(f)
    return f

def build_multi_arg(name, direction, params) -> MultiIOArg:
    """Pop this group's params out of `params` (mutates) and build a MultiIOArg."""
    # TODO proper logging here
    LOG.debug(f'name: {name}')
    LOG.debug(f'direction: {direction}')
    LOG.debug(f'params: {params}')
    prefix = f"{name}_"
    chosen = {}
    for k in [k for k in params if k.startswith(prefix)]:
        v = params.pop(k)
        if v:
            chosen[k[len(prefix):].replace("_", "-")] = v
    LOG.debug(f'chosen: {chosen}')
    if len(chosen) != 1:
        raise click.UsageError(f"Exactly one {name} {direction}-source required.")
    medium, value = next(iter(chosen.items()))
    if "show" in medium or "scan" in medium:
        medium = "cam"
    elif "json" in medium:
        medium = "json"
    elif "txt" in medium:
        medium = "txt"
    else:
        medium = "png"
    LOG.debug(f'medium: {medium}')
    LOG.debug(f'value: {value}')
    path = None if medium == "cam" else Path(value)
    return MultiIOArg(name, direction, medium, path)


# ---- plural versions

def _make_group_many(name, direction):
    title = f"{name.capitalize()} inputs" if direction == "in" else f"{name} outputs"
    return cloup.OptionGroup(title, constraint=RequireAtLeast(1))

def _add_options_many(f, name, mediums, direction):
    help_text = {  # (same dicts as before)
        "in": {
            "cam":  "Scan QR code(s) via the camera (repeatable).",
            "png":  "Load QR code from a png file (repeatable).",
            "txt":  "Load QR text (`egc:...`) from a file (repeatable).",
            "json": "Load from a JSON file (repeatable).",
        },
        "out": {
            "cam":  "Show QR code(s) so you can take pics of them.",
            "png":  "Save QR code as a png file (repeatable).",
            "txt":  "Save QR text (`egc:...`) to a file (repeatable).",
            "json": "Save to a JSON file (repeatable).",
        },
    }[direction]
    cli_verbs = {
        "in" : {"cam": "scan-qr", "png": "load-png", "json": "load-json", "txt": "load-txt"},
        "out": {"cam": "show-qr", "png": "save-png", "json": "save-json", "txt": "save-txt"},
    }[direction]
    group = _make_group_many(name, direction)

    factories = {
        # count=True -> repeatable flag; value is an int (number of times passed)
        "cam": lambda: group.option(
            f"--{name}-{cli_verbs['cam']}", count=True,
            help=help_text["cam"]),
        "png": lambda: group.option(
            f"--{name}-{cli_verbs['png']}", type=click.Path(), metavar="PATH",
            multiple=True, help=help_text["png"]),
        "txt": lambda: group.option(
            f"--{name}-{cli_verbs['txt']}", type=click.Path(), metavar="PATH",
            multiple=True, help=help_text["txt"]),
        "json": lambda: group.option(
            f"--{name}-{cli_verbs['json']}", type=click.Path(), metavar="PATH",
            multiple=True, help=help_text["json"]),
    }
    opts = [factories[m]() for m in mediums]
    for opt in reversed(opts):
        f = opt(f)
    return f

def build_multi_args(name, direction, params) -> list[MultiIOArg]:
    """Pop this group's params out of `params` (mutates), return a list of MultiIOArg."""
    prefix = f"{name}_"
    args: list[MultiIOArg] = []
    for k in [k for k in params if k.startswith(prefix)]:
        v = params.pop(k)
        if not v:
            continue
        suffix = k[len(prefix):]          # e.g. "load_png", "scan_qr"
        if "scan" in suffix or "show" in suffix:
            for _ in range(int(v)):       # count=True -> int
                args.append(MultiIOArg(name, direction, "cam", None))
        else:
            medium = ("json" if "json" in suffix
                      else "txt" if "txt" in suffix
                      else "png")
            for val in v:                 # multiple=True -> tuple
                args.append(MultiIOArg(name, direction, medium, Path(val)))
    if not args:
        raise click.UsageError(f"At least one {name} {direction}-source required.")
    LOG.debug(f'{name} args: {args}')
    return args

def multi_load_many(name, decode_cls, mediums, *, required=True):
    """`in`: gather repeated args, read+parse each to `decode_cls`, inject as `name` (a list)."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            pios = build_multi_args(name, "in", params)   # pops name_* keys
            results = []
            for pio in pios:
                n_attempts = 0
                while True:
                    n_attempts += 1
                    try:
                        results.append(_multi_read(pio, decode_cls=decode_cls))
                        break
                    except Exception as e:
                        LOG.error(e)
                        if n_attempts > 3:
                            raise
                        time.sleep(1)
            params[name] = results
            return fn(**params)
        return _add_options_many(wrapper, name, mediums, "in")
    return decorator


# ---- read / write --------------------------------------------------------

# This could be part of the interface, but can normally be automated via
# multi_load_arg below.
# TODO clean up/unify my json and dict handling with electionguard's way
def _multi_read(mio: MultiIOArg, decode_cls=None):
    match mio.medium:
        case "cam":  return scan_qrcode(decode_cls=decode_cls)
        case "png":  return load_qrcode(mio.path, decode_cls)
        case "txt":  return decode_cls.from_qr_str(mio.path.read_text())
        case "json":
            txt = mio.path.read_text()
            try:
                # If it's a native ElectgionGuard type,
                # deserialize the official way.
                # TODO will this attempt to deserialize even if not?
                return eg_serialize.from_raw(decode_cls, txt)
            except:
                # Otherwise, assume it's one of our from_json types.
                return decode_cls.from_json(txt)


# This can't be automated the same way, so it becomes par of the interface.
# Use inside a command after multi_save_arg has built the MultiIOArg.
def multi_save(mio: MultiIOArg, obj: Any, exist_ok=True) -> None:
    LOG.debug(f'mio: {mio}')
    if mio.path is not None and mio.path.exists() and not exist_ok:
        raise click.UsageError(f"path already exists: {mio.path}")
    match mio.medium:
        case "cam":  print_qrcode(obj)
        case "png":  save_qrcode(obj, mio.path)
        case "txt":  mio.path.write_text(obj.to_qr_str())
        case "json": mio.path.write_text(obj.to_json())
        case _: raise NotImplementedError


# ---- public decorators ---------------------------------------------------

def multi_load(name, decode_cls, mediums, *, required=True):
    """`in` direction: gather args, read + parse to `decode_cls`, inject as `name`."""
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(**params):
            pio = build_multi_arg(name, "in", params)      # pops name_* keys

            # TODO why does this sometimes fail? is it a race condition or something else?
            n_attempts = 0
            while True:
                n_attempts += 1
                try:
                    params[name] = _multi_read(pio, decode_cls=decode_cls)
                    LOG.debug(f'read {name} after {n_attempts} attempts')
                    break
                except Exception as e:
                    LOG.error(e)
                    if n_attempts > 3:
                        raise
                    time.sleep(1)

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
