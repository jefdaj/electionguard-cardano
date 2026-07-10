import click
from egc_app.cli import server
from egc_app.cli import election

@click.group()
def cli() -> None:
	pass

cli.add_command(server.server)
cli.add_command(election.election)

if __name__ == '__main__':
    cli()
