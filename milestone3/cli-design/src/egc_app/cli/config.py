import asyncio
import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the EGC node config."

@config.command()
def role():
    "Get current election role."
    cfg = asyncio.run(Client().config())
    role = cfg['role']
    click.echo(role)

# only needed for root_ctx in the merge below:
# @click.pass_context
# def save(ctx, out_json):
@config.command()
@click.argument("out_json", type=click.Path(dir_okay=False, writable=True))
def save(out_json):
    "Write your current config to JSON."

    # This works but seems counter-intuitive...
    # If you call: egc --config <in-json> config save <out-json>
    # You'll get <out-json> with overrides from <in-json>
    # TODO would that ever be useful?
    # root_ctx = ctx.find_root()
    # override = dict(root_ctx.default_map or {})
    # live = asyncio.run(Client().config())
    # saved = deep_merge(live, override)

    cfg = asyncio.run(Client().config())
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    click.echo(f"Saved config → {out_json}")
