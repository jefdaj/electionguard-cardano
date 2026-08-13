import asyncio
import click
from egc_app.cli.utils import RoleAwareGroup
from egc_app import schemas
from egc_app.client import Client
from egc_app.cli.utils import *

import logging
LOG = logging.getLogger(__name__)

@click.group(cls=RoleAwareGroup)
def channel() -> None:
    "Request, add, remove, or await channels."

@channel.command(roles=['admin'])
def add():
    "Add (mint) a subchannel."
    raise NotImplementedError

@channel.command(roles=['admin'])
def remove():
    "Remove (burn) a subchannel."
    raise NotImplementedError

@channel.command(name='await')
@click.option('--role', type=click.STRING, required=True)
def await_(role: str):
    """Wait for your channel to appear.

    This should normally be done by an observer. You can also use it once you
    have a role, but then it's more like an assert statement. The admin can
    also use this to wait for their channel from the funder.
    """
    ch_str = asyncio.run(Client().channel_await(role=role))
    click.echo(ch_str)

@channel.command(roles=['observer'])
@click.option('--role', type=click.STRING, required=True)
@multi_save_arg("request", ["cam", "png", "txt", "json"]) # TODO can it be "request"?
def request(role: str, request: MultiIOArg):
    """Create a channel request.

    You can communicate it to the election admin
    through any channel: qr code, email, etc. Then use `egc channel await` to
    wait until the admin has created your channel.

    Requests are automatically for the currently subscribed election, so you
    need to subscribe to one before running this.
    """
    data = asyncio.run(Client().channel_request(role=role))
    LOG.debug(f'data: {data}')
    multi_save(request, data, exist_ok=False)

@channel.command(roles=['admin'])
@multi_load_many("request", schemas.ChannelRequestOut, ["png", "txt", "json"]) # TODO also cam?
@click.option('--subchannel-ada', type=click.INT, default=20)
@click.option('--done-onboarding', is_flag=True, default=False)
def create(request: list[MultiIOArg], subchannel_ada: int, done_onboarding: bool):
    # click.echo(locals())
    asyncio.run(Client().channel_create(
        requests        = request, # singular above so each cli arg comes out right
        subchannel_ada  = subchannel_ada,
        done_onboarding = done_onboarding,
    ))
