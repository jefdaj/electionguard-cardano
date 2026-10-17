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
    click.echo(resp)

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
    click.echo(resp)

@cli.command()
@click.option('--policy-id', type=click.STRING)
@click.option('--slot-no', type=click.INT)
@click.option('--block-header-hash', type=click.STRING)
def subscribe(policy_id, slot_no, block_header_hash):
    resp = asyncio.run(Client().subscribe(policy_id, slot_no, block_header_hash))
    click.echo(resp)

# TODO observe
# TODO init_election

if __name__ == '__main__':
    cli()
