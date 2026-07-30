from fastapi import APIRouter, Depends, Request
from dataclasses import asdict
from egc_app.server.state import get_state, reset_election_state
from egc import *
import asyncio

import logging
LOG = logging.getLogger(__name__)

router = APIRouter(prefix="/subscription")

# TODO GET /subscription?

@router.put("")
async def start_subscriber(config: ElectionConfig, state=Depends(get_state)):

    # Reset election-specific state, leaving alone the config, wallet, etc
    reset_election_state(state)

    state.config['election'] = asdict(config)

    state.node = ObserverNode(
        role_index = 1, # TODO pass this in
        wallet     = state.wallet,
    )

    def log_event(event: ChannelEvent) -> None:
        LOG.debug(f'election event:\n{event.to_raw()}')

    def log_error(err: ElectionError) -> None:
        LOG.error(f'election error:\n{err.to_raw()}')

    state.node.subscribe(
        config,
        on_event = log_event,
        on_error = log_error,
    )

    return 201
