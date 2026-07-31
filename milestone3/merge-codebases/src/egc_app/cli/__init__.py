import click
import json

from egc_app.cli.utils import *


### main CLI ###

from egc_app.cli import ballot
from egc_app.cli import batch
from egc_app.cli import ceremony
from egc_app.cli import channel
from egc_app.cli import collateral
from egc_app.cli import config
from egc_app.cli import election
from egc_app.cli import manifest
from egc_app.cli import node
from egc_app.cli import phase
from egc_app.cli import spoiled
from egc_app.cli import tally
from egc_app.cli import verification
from egc_app.cli import wallet

@click.group(cls=RoleAwareGroup, invoke_without_command=True)
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False),
    required=False,
)
@click.option(
    "--role",
    envvar="CLI_ROLE",
    default="observer",
    show_default=True,
    type=click.Choice(CLI_ROLES, case_sensitive=False),
)
@click.pass_context
def cli(ctx, config, role):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())

cli.add_command(ballot.ballot)
cli.add_command(batch.batch)
cli.add_command(ceremony.ceremony)
cli.add_command(channel.channel)
cli.add_command(collateral.collateral)
cli.add_command(config.config)
cli.add_command(election.election)
cli.add_command(manifest.manifest)
cli.add_command(node.node)
cli.add_command(phase.phase)
cli.add_command(spoiled.spoiled)
cli.add_command(tally.tally)
cli.add_command(verification.verification)
cli.add_command(wallet.wallet)


### list commands ###

# TODO remove? not sure if useful except for development

def iter_commands(cmd, ctx, prefix=""):
    yield prefix.strip()
    if isinstance(cmd, click.Group):
        for name in cmd.list_commands(ctx):
            sub = cmd.get_command(ctx, name)
            if sub is None:
                continue
            yield from iter_commands(sub, ctx, f"{prefix} {name}")

@cli.command()
@click.pass_context
def list_commands(ctx):
    root = ctx.find_root().command
    for path in sorted(filter(None, iter_commands(root, ctx))):
        if not ' ' in path:
            continue
        click.echo(path)


if __name__ == '__main__':
    cli()
