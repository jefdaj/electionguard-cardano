import asyncio
import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the EGC node config."

def get_cfg(section=None):
    cfg = asyncio.run(Client().config())
    if section is None:
        return cfg
    if not section in cfg:
        return {}
    return cfg[section]

# TODO remove?
@config.command()
def all():
    "Get the complete config as JSON."
    cfg = get_cfg()
    click.echo(json.dumps(cfg, indent=2))

@config.command()
def node():
    "Get current node config as JSON."
    cfg = get_cfg(section='node')
    click.echo(json.dumps(cfg, indent=2))

@config.command()
def election():
    "Get current election config as JSON."
    cfg = get_cfg(section='election')
    click.echo(json.dumps(cfg, indent=2))

@config.command()
def batch():
    "Get current batch config as JSON."
    cfg = get_cfg(section='batch')
    click.echo(json.dumps(cfg, indent=2))

@config.command()
def role():
    "Get current election role."
    role = get_cfg(section='role')
    if not role:
        role = 'any' # TODO default to observer
    click.echo(role)

@config.command()
@click.argument("out_json", type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def save(ctx, out_json):
    "Write your current config to JSON."

    root_ctx = ctx.find_root()
    saved = dict(root_ctx.default_map or {})

    # Merge live server state on top — wins over stored defaults
    live = asyncio.run(Client().config())
    saved = deep_merge(saved, live)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)
    click.echo(f"Saved config → {out_json}")
