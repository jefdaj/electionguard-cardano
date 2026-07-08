import click, asyncio

from egc_app.client import Client
from egc_app.server.run import run_server

import logging
LOG = logging.getLogger(__name__)

@click.group()
def cli() -> None:
	pass

@cli.command()
def serve():
    run_server()

@cli.command()
def health():
    resp = asyncio.run(Client().health())
    print(resp)

# TODO remove
@cli.command()
@click.argument("n", type=int)
def incr(n):
    LOG.debug('incr')
    LOG.debug(f'n: {n}')
    asyncio.run(Client().incr(n))

# TODO remove
@cli.command()
def state():
    resp = asyncio.run(Client().state())
    print(resp)

# TODO repl? something like:
# @cli.command()
# def repl():
#     """Interactive session."""
#     c = Client()
#     while True:
#         cmd = click.prompt("egc", type=str)
#         if cmd in ("quit", "exit"):
#             break
#         # dispatch cmd to client...
#         click.echo(asyncio.run(c.run(cmd)))

if __name__ == '__main__':
    cli()
