import click

from egc_app.cli import ballot
from egc_app.cli import batch
from egc_app.cli import ceremony
from egc_app.cli import channel
from egc_app.cli import config
from egc_app.cli import election
from egc_app.cli import manifest
from egc_app.cli import phase
from egc_app.cli import server
from egc_app.cli import server
from egc_app.cli import spoiled
from egc_app.cli import tally
from egc_app.cli import verification

@click.group()
def cli() -> None:
	pass

cli.add_command(ballot.ballot)
cli.add_command(batch.batch)
cli.add_command(ceremony.ceremony)
cli.add_command(channel.channel)
cli.add_command(config.config)
cli.add_command(election.election)
cli.add_command(manifest.manifest)
cli.add_command(phase.phase)
cli.add_command(server.server)
cli.add_command(server.server)
cli.add_command(spoiled.spoiled)
cli.add_command(tally.tally)
cli.add_command(verification.verification)

if __name__ == '__main__':
    cli()
