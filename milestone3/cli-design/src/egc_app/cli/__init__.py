import click
import json

from egc_app.cli.utils import *

from egc_app.cli import ballot
from egc_app.cli import batch
from egc_app.cli import ceremony
from egc_app.cli import channel
from egc_app.cli import config
from egc_app.cli import election
from egc_app.cli import manifest
from egc_app.cli import node
from egc_app.cli import phase
from egc_app.cli import spoiled
from egc_app.cli import tally
from egc_app.cli import verification

@click.group(cls=RoleAwareGroup, invoke_without_command=True)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--role",
    envvar="CLI_ROLE",
    default="any",
    show_default=True,
    type=click.Choice(CLI_ROLES, case_sensitive=False),
)
@click.pass_context
def cli(ctx, config, role):
    if config:
        with open(config, "r", encoding="utf-8") as f:
            config_defaults = json.load(f)
    else:
        config_defaults = {}
    env_defaults = env_to_default_map()
    ctx.ensure_object(dict)
    ctx.default_map = deep_merge(config_defaults, env_defaults)
    ctx.obj["role"] = role.lower()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

cli.add_command(ballot.ballot)
cli.add_command(batch.batch)
cli.add_command(ceremony.ceremony)
cli.add_command(channel.channel)
cli.add_command(config.config)
cli.add_command(election.election)
cli.add_command(manifest.manifest)
cli.add_command(node.node)
cli.add_command(phase.phase)
cli.add_command(spoiled.spoiled)
cli.add_command(tally.tally)
cli.add_command(verification.verification)

if __name__ == '__main__':
    cli()
