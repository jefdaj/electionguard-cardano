import asyncio
import click
import json
from egc_app.client import Client
from egc_app.cli.utils import *

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the EGC node config."

@config.command()
def show():
    """Print your current config as JSON.
    Use jq to access fields if needed.
    Examples:

    \b
        MY_PORT=$(egc config show | jq -r '.node.port')
        MY_PRIV_DIR="$(egc config show | jq -r '.node.private_dir')"
    """
    cfg = asyncio.run(Client().config())
    click.echo(json.dumps(cfg))

@config.command()
@click.argument("out_json", type=click.Path(dir_okay=False, writable=True))
def save(out_json):
    "Write your current config to JSON."
    cfg = asyncio.run(Client().config())
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    click.echo(f"Saved config → {out_json}")

# TODO remove in favor of config show | jq?
@config.command()
@click.pass_context
def role(ctx):
    "Print your current election role."
    cfg = asyncio.run(Client().config())
    click.echo(cfg['node']['role'])
