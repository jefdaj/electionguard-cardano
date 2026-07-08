import click, asyncio

# TODO relative?
from egc_client.lib import Client

@click.group()
def cli() -> None:
	pass

@cli.command()
@click.argument("n", type=int)
def incr(n):
    asyncio.run(Client().incr())

@cli.command()
def state(n):
    asyncio.run(Client().state())

# interactive command
@cli.command()
def repl():
    """Interactive session."""
    c = Client()
    while True:
        cmd = click.prompt("egc", type=str)
        if cmd in ("quit", "exit"):
            break
        # dispatch cmd to client...
        click.echo(asyncio.run(c.run(cmd)))

if __name__ == '__main__':
    cli()
