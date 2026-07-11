import click
import json
from egc_app.cli.utils import RoleAwareGroup, deep_merge

@click.group(cls=RoleAwareGroup)
def config() -> None:
    "View and manage the current EGC node config."

@config.command()
def node():
    pass

@config.command()
def election():
    pass

@config.command()
def batch():
    pass

@config.command()
def role():
    pass

@config.command()
@click.argument("out_json", type=click.Path(dir_okay=False, writable=True))
@click.pass_context
def save(ctx, out_json):
    "Write the current config to JSON."

    root_ctx = ctx.find_root()
    saved = dict(root_ctx.default_map or {})

    # Merge live server state on top — wins over stored defaults
    # live = fetch_live_state(ctx.obj) # TODO write this
    live = {}
    saved = deep_merge(saved, live)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)
    click.echo(f"Saved config → {out_json}")
