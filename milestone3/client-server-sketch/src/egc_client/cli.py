import click, asyncio

# TODO relative?
from egc_client.lib import Client

import logging

LOG = logging.getLogger(__name__)

@click.group()
def cli() -> None:
	pass

@cli.command()
def health():
    resp = asyncio.run(Client().health())
    print(resp)

@cli.command()
@click.argument("n", type=int)
def incr(n):
    LOG.debug('incr')
    LOG.debug(f'n: {n}')
    asyncio.run(Client().incr(n))

@cli.command()
def state():
    resp = asyncio.run(Client().state())
    print(resp)

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
