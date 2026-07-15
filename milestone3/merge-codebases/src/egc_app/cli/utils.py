from __future__ import annotations
from typing import Iterable
import click
import cloup
from cloup.constraints import mutually_exclusive, require_one
import os
import asyncio
from egc_app.client import Client
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import functools
import json as _json # json conflicts with payload_io


### config parsing ###


def get_cli_config(config):
    if config:
        with open(config, "r", encoding="utf-8") as f:
            return _json.load(f)
    else:
        return {}

def get_node_config():
    try:
        return asyncio.run(Client().config())
    except:
        return {}

def get_env_config(prefix="EGC_"):
    "Parse simple env vars into a default map."
    out = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].lower().split("_")
        if len(parts) < 3:
            continue
        group, command = parts[0], parts[1]
        option = "_".join(parts[2:])
        out.setdefault(group, {}).setdefault(command, {})[option] = value
    return out

def deep_merge(base: dict, override: dict) -> dict:
    "Merge options from env vars with options from config file."
    result = dict(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def _peek_arg(args: list[str], flag: str) -> str | None:
    """Read --flag VALUE or --flag=VALUE from raw args without consuming them."""
    for i, arg in enumerate(args):
        if arg == flag and i + 1 < len(args):
            return args[i + 1]
        if arg.startswith(f"{flag}="):
            return arg.split("=", 1)[1]
    return None


def _build_default_map(config_path: str | None, role: str) -> dict:
    from_cli  = get_cli_config(config_path)
    from_env  = get_env_config()
    from_node = get_node_config()
    dm = deep_merge(
        deep_merge(from_cli, from_node),
        from_env,
        # deep_merge(from_env, {"role": role}),
    )
    dm["role"] = role  # CLI/env always wins
    return dm


### role-aware group ###

# TODO remove 'any'?
# TODO enum type
CLI_ROLES = ('any', 'admin', 'guardian', 'device', 'verifier', 'observer')

class RoleAwareGroup(cloup.Group):

    def make_context(
        self,
        info_name: str,
        args: list[str],
        parent: click.Context | None = None,
        **kwargs,
    ) -> click.Context:
        # Build default_map early at root so --help and eager options
        # see the correct role before the callback ever runs.
        if parent is None:
            config_path = _peek_arg(args, "--config")
            role = _peek_arg(args, "--role") or os.environ.get("CLI_ROLE", "observer")
            kwargs.setdefault("default_map", _build_default_map(config_path, role))
        return super().make_context(info_name, args, parent=parent, **kwargs)

    def _role(self, ctx: click.Context) -> str:
        return (ctx.find_root().default_map or {}).get("role", "observer")

    def _allowed(self, ctx: click.Context, cmd: click.Command) -> bool:
        role = self._role(ctx)
        if role == "any":
            return True
        roles = getattr(cmd, "roles", frozenset())
        return not roles or role in roles

    def _has_visible_descendant(self, ctx: click.Context, group: click.Group) -> bool:
        for name, cmd in group.commands.items():
            if isinstance(cmd, click.Group):
                if self._has_visible_descendant(ctx, cmd):
                    return True
            elif self._allowed(ctx, cmd):
                return True
        return False

    def list_commands(self, ctx: click.Context) -> list[str]:
        visible = []

        for name, cmd in sorted(self.commands.items()):
            if isinstance(cmd, click.Group):
                if self._has_visible_descendant(ctx, cmd):
                    visible.append(name)
            elif self._allowed(ctx, cmd):
                visible.append(name)

        return visible

    def get_command(self, ctx: click.Context, name: str):
        return self.commands.get(name)

    def resolve_command(self, ctx: click.Context, args: list[str]):
        cmd_name, cmd, remaining = super().resolve_command(ctx, args)
        if cmd is not None and not isinstance(cmd, click.Group) and not self._allowed(ctx, cmd):
            raise click.ClickException("Permission denied")
        return cmd_name, cmd, remaining

    def command(self, *args, roles=None, **kwargs):
        def decorator(f):
            cmd = cloup.command(*args, **kwargs)(f)
            cmd.roles = frozenset(roles or ())
            self.add_command(cmd)
            return cmd
        return decorator

    def group(self, *args, **kwargs):
        kwargs.setdefault("cls", type(self))

        def decorator(f):
            grp = cloup.group(*args, **kwargs)(f)
            self.add_command(grp)
            return grp
        return decorator

    def format_commands(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        rows = []
        for name in self.list_commands(ctx):  # list_commands already filters by role
            cmd = self.get_command(ctx, name)
            if cmd is None:
                continue
            rows.append((name, cmd.get_short_help_str()))

        if not rows:
            role = self._role(ctx)
            formatter.write(f"\nNo {role} commands here.\n")
            return

        role = self._role(ctx)
        label = f"{role.replace("any", "all").capitalize()} commands"
        with formatter.section(label):
            formatter.write_dl(rows)


def _parse_roles_and_args(first, rest, kwargs):
    if first is None:
        return frozenset(), rest
    if isinstance(first, (list, tuple, set, frozenset)):
        return frozenset(first), rest
    if "roles" in kwargs:
        return frozenset(kwargs.pop("roles") or ()), (first, *rest)
    return frozenset(), (first, *rest)


def role_command(first=None, /, *cmd_args, **cmd_kwargs):
    "Use this in place of click.command"

    roles, cmd_args = _parse_roles_and_args(first, cmd_args, cmd_kwargs)

    def deco(f):
        cmd = click.command(*cmd_args, **cmd_kwargs)(f)
        cmd.roles = roles
        return cmd

    return deco


def role_group(first=None, /, *grp_args, **grp_kwargs):
    "Use this in place of click.group"

    roles, grp_args = _parse_roles_and_args(first, grp_args, grp_kwargs)

    def deco(f):
        grp = click.group(*grp_args, cls=RoleAwareGroup, **grp_kwargs)(f)
        grp.roles = roles
        return grp

    return deco


### IO decorators ###

# TODO better name than "endpoint"?

Direction = Literal["in", "out"]
Medium = Literal["qr", "qr-image", "json"]

@dataclass
class Endpoint:
    direction: Direction
    medium: Medium
    path: Path | None = None

def resolve_endpoint(direction: Direction, **params) -> Endpoint:
    prefix = f"{direction}_"
    # collect only this direction's medium params
    chosen = {
        k[len(prefix):].replace("_", "-"): v
        for k, v in params.items()
        if k.startswith(prefix) and v
    }
    if len(chosen) != 1:
        raise click.UsageError("Exactly one data source/destination required.")
    medium, value = next(iter(chosen.items()))
    path = None if medium == "qr" else Path(value)
    return Endpoint(direction, medium, path)


def payload_io(*mediums, direction=None, required=True):
    """Attach QR/JSON source-or-destination options as a constrained group.

    mediums:   any of "qr", "qr-image", "json".
    direction: None | "in" | "out". When set, flags are prefixed
               (e.g. --out-qr) and help verbs reflect the direction.
    required:  True  -> require_one (exactly one medium must be given)
               False -> mutually_exclusive (at most one)
    """
    prefix = f"{direction}-" if direction else ""
    verb = {"in": "Read", "out": "Write"}.get(direction, "Read/write")

    group = cloup.OptionGroup(
        "Data source / destination",
        constraint=(require_one if required else mutually_exclusive),
    )

    def _qr():
        return group.option(
            f"--{prefix}qr", is_flag=True,
            help=f"{verb} a QR code via the camera / screen.",
        )

    def _qr_image():
        return group.option(
            f"--{prefix}qr-image", type=click.Path(), metavar="PATH",
            help=f"{verb} a QR code as an image file.",
        )

    # simpler: let Click derive the dest normally
    def _json():
        return group.option(
            f"--{prefix}json", type=click.Path(), metavar="PATH",
            help=f"{verb} data as a JSON file.",
        )

    factories = {"qr": _qr, "qr-image": _qr_image, "json": _json}
    opts = [factories[m]() for m in mediums]

    def decorator(f):
        for opt in reversed(opts): # reverse -> declaration order in --help
            f = opt(f)
        return f

    return decorator


def read_endpoint(ep: Endpoint) -> bytes:
    match ep.medium:
        case "qr":       return scan_qr_camera()
        case "qr-image": return decode_qr_image(ep.path)
        case "json":     return ep.path.read_bytes()

def write_endpoint(ep: Endpoint, data: bytes) -> None:
    match ep.medium:
        case "qr":       show_qr_screen(data)
        case "qr-image": encode_qr_image(data, ep.path)
        case "json":     ep.path.write_bytes(data)

def run_endpoint(ep: Endpoint, data: bytes | None = None):
    return read_endpoint(ep) if ep.direction == "in" else write_endpoint(ep, data)

# TODO remove? or is it useful?
def io_command(direction, *mediums, **cmd_kw):
    """Decorator: cloup command + payload_io + auto-resolved endpoint."""
    def decorator(fn):
        @cloup.command(**cmd_kw)
        @payload_io(*mediums, direction=direction)
        @functools.wraps(fn)
        def wrapper(**params):
            ep = resolve_endpoint(direction, **params)
            return fn(ep, **{k: v for k, v in params.items()
                             if not k.startswith(f"{direction}_")})
        return wrapper
    return decorator

# usage examples:

# @io_command("out", "qr", "qr-image", "json")
# def request(ep: Endpoint):
#     write_endpoint(ep, build_role_request(...))

# @io_command("in", "qr-image", "json")
# def subscription(ep: Endpoint):
#     store_subscription(parse_subscription(read_endpoint(ep)))
