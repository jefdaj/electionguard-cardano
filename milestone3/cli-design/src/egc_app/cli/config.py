import asyncio
import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the current EGC node config."

@config.command()
def node():
    "Get your current node API URL."

@config.command()
def election():
    "Get your current election config."

@config.command()
def batch():
    "Get your current batch config."

@config.command()
def role():
    "Get your current election role."

@config.command()
@click.argument("out_json", type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def save(ctx, out_json):
    "Write your current config to JSON."

    root_ctx = ctx.find_root()
    saved = dict(root_ctx.default_map or {})

    # Merge live server state on top — wins over stored defaults
    live = asyncio.run(Client().node_config())
    saved = deep_merge(saved, live)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)
    click.echo(f"Saved config → {out_json}")
